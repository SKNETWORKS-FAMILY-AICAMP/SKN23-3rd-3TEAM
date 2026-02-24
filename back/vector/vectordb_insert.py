import json
import argparse
import chromadb

from pathlib import Path
from chromadb.utils import embedding_functions

# [DB 설정] - DB 교체 시 이 섹션 수정
DEFAULT_DATA_DIR = "./assets/vector_data"                       # JSON 파일이 위치한 폴더
ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH  = str(ROOT_DIR / "vector_store")                       # 벡터DB 로컬 저장 경로
COLLECTION_NAME = "skin_knowledge_base"                         # 컬렉션(인덱스)명
EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"                # 한국어 특화 (권장)
# EMBED_MODEL_NAME = "BAAI/bge-large-zh-v1.5"                   # 대안 1
# EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # 대안 2 (다국어)
REQUIRED_FIELDS = ["id", "doc_type", "category", "content"]     # 유효성 검사

def validate_document(doc: dict, index: int) -> bool:
    """필수 필드 존재 여부 확인"""
    for field in REQUIRED_FIELDS:
        if field not in doc or not doc[field]:
            print(f"    [SKIP] 문서 #{index} ({doc.get('id', 'unknown')}): '{field}' 필드 누락")

            return False

    return True

# JSON 파일 목록 수집
def collect_json_files(data_dir: str = None, file_list: list[str] = None) -> list[Path]:
    """
    처리할 JSON 파일 목록 반환
    - file_list 지정 시: 해당 파일들만 처리
    - data_dir 지정 시: 폴더 내 모든 .json 파일 처리
    """
    if file_list:
        paths = [Path(f) for f in file_list]
        missing = [p for p in paths if not p.exists()]

        if missing:
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {[str(p) for p in missing]}")

        return sorted(paths)

    dir_path = Path(data_dir or DEFAULT_DATA_DIR)

    if not dir_path.exists():
        raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {dir_path}")

    files = sorted(dir_path.glob("*.json"))

    if not files:
        raise FileNotFoundError(f"폴더에 JSON 파일이 없습니다: {dir_path}")

    return files

# JSON 로드
def load_json(file_path: Path) -> list[dict]:
    raw = file_path.read_text(encoding="utf-8").strip()

    # 배열 형식 시도
    try:
        data = json.loads(raw)

        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    # 객체 나열 형식 파싱 - 중괄호 블록 단위로 분리
    documents = []
    depth = 0
    start = None

    for i, ch in enumerate(raw):
        if ch == '{':
            if depth == 0:
                start = i

            depth += 1
        elif ch == '}':
            depth -= 1

            if depth == 0 and start is not None:
                block = raw[start:i+1].strip()
                try:
                    documents.append(json.loads(block))
                except json.JSONDecodeError as e:
                    print(f"    [WARN] JSON 파싱 실패 (위치 {start}~{i}): {e}")
                start = None

    return documents

# 메타데이터 변환
def build_metadata(doc: dict) -> dict:
    base = {
        "doc_type":       str(doc.get("doc_type", "")),
        "category":       str(doc.get("category", "")),
        "skin_type":      ",".join(doc.get("skin_type", [])),
        "concern_tag":    ",".join(doc.get("concern_tag", [])),
        "ingredient_tag": ",".join(doc.get("ingredient_tag", [])),
        "source":         str(doc.get("source", "internal")),
        "chunk_index":    int(doc.get("chunk_index", 0)),
    }

    # doc_type별 확장 메타 — 없는 필드는 그냥 무시
    EXTRA_FIELDS = {
        "cosmetic_product": [
            "item_name", "entp_name", "report_type",
            "manuf_country", "cosmetic_std", "target_type",
            "spf", "pa", "water_proof",
            "effect_whitening", "effect_antiaging", "effect_suncare",
            "cancel_yn",
        ],
    }

    for field in EXTRA_FIELDS.get(doc.get("doc_type", ""), []):
        val = doc.get(field, "")
        
        if val is not None:
            base[field] = str(val)

    return base

# [DB 클라이언트 초기화] - DB 교체 시 이 함수 교체
def get_db_collection():
    client = chromadb.PersistentClient(path=DB_PATH)

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL_NAME
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}  # 유사도 계산: cosine similarity
    )

    return collection

# 파일 단위 Insert
def insert_from_file(file_path: Path, collection) -> tuple[int, int]:
    print(f"\n  📄 {file_path.name}")

    documents = load_json(file_path)

    print(f"     로드: {len(documents)}건")

    # 1. 유효성 검사 통과한 문서만 수집
    valid_docs = []
    skip_count = 0

    for i, doc in enumerate(documents):
        if not validate_document(doc, i):
            skip_count += 1
            continue
        valid_docs.append(doc)

    if not valid_docs:
        print(f"     Insert할 문서 없음 (전부 유효성 실패)")
        return 0, skip_count

    # 2. 기존 ID를 한 번의 bulk 조회로 확인
    candidate_ids = [doc["id"] for doc in valid_docs]
    existing = collection.get(ids=candidate_ids, include=[])
    existing_set = set(existing["ids"])

    dup_count = len(existing_set)
    if dup_count:
        print(f"     중복 스킵: {dup_count}건")
    skip_count += dup_count

    # 3. 새 문서만 필터링
    ids       = []
    contents  = []
    metadatas = []

    for doc in valid_docs:
        if doc["id"] in existing_set:
            continue
        ids.append(doc["id"])
        contents.append(doc["content"])
        metadatas.append(build_metadata(doc))

    if not ids:
        print(f"     Insert할 문서 없음 (전부 중복)")
        return 0, skip_count

    # 4. 배치 단위 Insert
    BATCH_SIZE = 5000
    total_inserted = 0

    for start in range(0, len(ids), BATCH_SIZE):
        batch_ids       = ids[start:start + BATCH_SIZE]
        batch_contents  = contents[start:start + BATCH_SIZE]
        batch_metadatas = metadatas[start:start + BATCH_SIZE]

        collection.add(ids=batch_ids, documents=batch_contents, metadatas=batch_metadatas)

        total_inserted += len(batch_ids)
        print(f"     배치 insert: {total_inserted}/{len(ids)}건")

    print(f"     성공: {total_inserted}건 / 스킵: {skip_count}건")

    return total_inserted, skip_count

# 전체 Insert 실행
def insert_documents(data_dir: str = None, file_list: list[str] = None):
    # 1. JSON 파일 목록 수집
    json_files = collect_json_files(data_dir=data_dir, file_list=file_list)

    print(f"\n[1] 처리할 JSON 파일: {len(json_files)}개")

    for f in json_files:
        print(f"    - {f}")

    # 2. DB 초기화 (파일마다 재초기화하지 않고 한 번만)
    print(f"\n[2] 벡터DB 초기화 (경로: {DB_PATH})")
    print(f"[3] 임베딩 모델 로드: {EMBED_MODEL_NAME}")

    collection = get_db_collection()

    print(f"[4] 컬렉션: {COLLECTION_NAME}  (현재 {collection.count()}건 저장됨)")

    # 3. 파일별 순차 Insert
    print(f"\n[5] 파일별 Insert 시작")

    total_success = 0
    total_skip    = 0

    for file_path in json_files:
        success, skip = insert_from_file(file_path, collection)
        total_success += success
        total_skip    += skip

    # 4. 최종 결과 요약
    print(f"\n{'=' * 55}")
    print(f"  전체 Insert 완료")
    print(f"  - 처리 파일:      {len(json_files)}개")
    print(f"  - 성공:           {total_success}건")
    print(f"  - 건너뜀:         {total_skip}건")
    print(f"  - 컬렉션 총 문서: {collection.count()}건")
    print(f"{'=' * 55}")

# 검색 테스트 (Insert 후 확인용)
def search_test():
    print("\n[검색 테스트]")

    collection = get_db_collection()

    query = "건조한 피부 장벽 관리 성분"

    print(f"  쿼리: '{query}'")
    print(f"  필터: doc_type=ingredient, category=barrier\n")

    results = collection.query(
        query_texts=[query],
        n_results=3,
        where={
            "$and": [
                {"doc_type": {"$eq": "ingredient"}},
                {"category": {"$eq": "barrier"}},
            ]
        },
        include=["documents", "metadatas", "distances"]
    )

    for i, (doc_id, doc, meta, dist) in enumerate(zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    )):
        print(f"  --- 결과 {i+1} ---")
        print(f"  ID            : {doc_id}")
        print(f"  유사도 거리   : {dist:.4f}")
        print(f"  ingredient_tag: {meta.get('ingredient_tag')}")
        print(f"  내용 미리보기 : {doc[:60]}...")
        print()

# 메인 실행 코드
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="벡터DB Insert 스크립트")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--files", type=str, nargs="+", default=None,
        help="Insert할 JSON 파일 경로 (여러 개 가능, 예: --files a.json b.json)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Insert 후 검색 테스트 실행"
    )
    args = parser.parse_args()

    insert_documents(data_dir=DEFAULT_DATA_DIR, file_list=args.files)

    if args.test:
        search_test()