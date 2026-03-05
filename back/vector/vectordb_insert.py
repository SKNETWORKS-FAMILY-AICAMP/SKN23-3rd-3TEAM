import os
import json
import gdown
import argparse
import chromadb

from pathlib import Path
from chromadb.utils import embedding_functions

# [DB 설정] - DB 교체 시 이 섹션 수정
DEFAULT_DATA_DIR = "./assets/vector_data"                       # JSONL 파일이 위치한 폴더
ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH  = str(ROOT_DIR / "vector_store")                       # 벡터DB 로컬 저장 경로
COLLECTION_NAME = "skin_knowledge_base"                         # 컬렉션(인덱스)명
EMBED_MODEL_NAME = "jhgan/ko-sroberta-multitask"                # 한국어 특화 (권장)
# EMBED_MODEL_NAME = "BAAI/bge-large-zh-v1.5"                   # 대안 1
# EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"  # 대안 2 (다국어)
REQUIRED_FIELDS = ["id", "doc_type", "category", "content"]     # 유효성 검사

# 구글드라이브 파일 다운로드
def download_large_files():
    '''github에 업로드 하지 못하는 100MB 이상의 파일들은 구글드라이브에 업로드한 뒤 다운로드 받아 사용'''
    os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)

    files = {
        "mfds_cosmetic_report.jsonl": "1dS7bVoGj5ftaQfB1o5Pl1RRoswEfkWHk",
    }

    for filename, file_id in files.items():
        filepath = os.path.join(DEFAULT_DATA_DIR, filename)

        if os.path.exists(filepath):
            print(f"{filename} 이미 존재, 스킵")

            continue
        
        print(f"{filename} 다운로드 중...")

        gdown.download(id=file_id, output=filepath, quiet=False)

        print(f"{filename} 다운로드 완료")

def validate_document(doc: dict, index: int) -> bool:
    """필수 필드 존재 여부 확인"""
    for field in REQUIRED_FIELDS:
        if field not in doc or not doc[field]:
            print(f"    [SKIP] 문서 #{index} ({doc.get('id', 'unknown')}): '{field}' 필드 누락")

            return False

    return True

# JSONL 파일 목록 수집
def collect_json_files(data_dir: str = None, file_list: list[str] = None) -> list[Path]:
    """
    처리할 JSONL 파일 목록 반환
    - file_list 지정 시: 해당 파일들만 처리
    - data_dir 지정 시: 폴더 내 모든 .jsonl 파일 처리
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

    files = sorted(dir_path.glob("*.jsonl"))

    if not files:
        raise FileNotFoundError(f"폴더에 JSONL 파일이 없습니다: {dir_path}")

    return files

# JSONL 제너레이터 로드
def iter_jsonl(file_path: Path):
    """JSONL 파일을 한 줄씩 읽어 dict를 yield하는 제너레이터"""
    with open(file_path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"    [WARN] JSON 파싱 실패 (라인 {line_no}): {e}")

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

# 버퍼 단위 중복 검사 + Insert 헬퍼
def _flush_buffer(docs: list[dict], collection) -> tuple[int, int]:
    """buffer 단위로 기존 ID 중복 검사 후 신규 문서만 insert"""
    candidate_ids = [doc["id"] for doc in docs]
    existing = collection.get(ids=candidate_ids, include=[])
    existing_set = set(existing["ids"])

    dup_count = len(existing_set)

    ids, contents, metadatas = [], [], []
    for doc in docs:
        if doc["id"] not in existing_set:
            ids.append(doc["id"])
            contents.append(doc["content"])
            metadatas.append(build_metadata(doc))

    if ids:
        collection.add(ids=ids, documents=contents, metadatas=metadatas)

    return len(ids), dup_count

# 파일 단위 Insert (제너레이터 기반 청크 스트리밍)
def insert_from_file(file_path: Path, collection) -> tuple[int, int]:
    print(f"\n  📄 {file_path.name}")

    BATCH_SIZE = 5000
    total_inserted = 0
    total_skip = 0
    total_load = 0
    buffer = []

    for doc in iter_jsonl(file_path):
        total_load += 1

        if not validate_document(doc, total_load):
            total_skip += 1
            continue

        buffer.append(doc)

        if len(buffer) >= BATCH_SIZE:
            ins, skp = _flush_buffer(buffer, collection)
            total_inserted += ins
            total_skip += skp
            buffer.clear()
            print(f"     배치 insert: {total_inserted}건 처리됨")

    if buffer:
        ins, skp = _flush_buffer(buffer, collection)
        total_inserted += ins
        total_skip += skp

    print(f"     로드: {total_load}건")
    print(f"     성공: {total_inserted}건 / 스킵: {total_skip}건")

    return total_inserted, total_skip

# 전체 Insert 실행
def insert_documents(data_dir: str = None, file_list: list[str] = None):
    # 1. JSON 파일 목록 수집
    json_files = collect_json_files(data_dir=data_dir, file_list=file_list)

    print(f"\n[1] 처리할 JSONL 파일: {len(json_files)}개")

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
def search_test(query):
    print("\n[검색 테스트]")

    collection = get_db_collection()

    print(f"  쿼리: '{query}'")

    results = collection.query(
        query_texts=[query],
        n_results=3,
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
        print(f"  source: {meta.get('source')}")
        print(f"  내용 미리보기 : {doc[:60]}...")
        print()

# 메인 실행 코드
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="벡터DB Insert 스크립트")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--files", type=str, nargs="+", default=None,
        help="Insert할 JSONL 파일 경로 (여러 개 가능, 예: --files a.jsonl b.jsonl)"
    )
    args = parser.parse_args()

    if not args.files:
        try:
            download_large_files()
        except Exception as e:
            print(f"[ERROR] 파일 다운로드 실패: {e}")

            exit(1)

    insert_documents(data_dir=DEFAULT_DATA_DIR, file_list=args.files)