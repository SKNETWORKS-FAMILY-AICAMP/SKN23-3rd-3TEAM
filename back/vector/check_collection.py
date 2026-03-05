"""
ChromaDB 컬렉션 현황 확인 & 데이터 조회 스크립트
===================================================
옵션 없이 실행하면 전체 통계를 출력하고, 필터 옵션을 주면 특정 데이터를 조회

사용법:
    # 전체 통계 (기본)
    python check_collection.py

    # 전체 source 분포 + ID 샘플
    python check_collection.py --list-sources

    # source로 조회
    python check_collection.py --source derma_kr
    python check_collection.py --source aad_org
    python check_collection.py --source mfds_api

    # id 접두어로 조회
    python check_collection.py --id-prefix derma_disease
    python check_collection.py --id-prefix aad_

    # doc_type으로 조회
    python check_collection.py --doc-type guide
    python check_collection.py --doc-type ingredient

    # 출력 건수 조절 (기본 5)
    python check_collection.py --source derma_kr --limit 10
"""

import argparse
import chromadb

from pathlib import Path
from collections import Counter

ROOT_DIR = Path(__file__).resolve().parents[2]
DB_PATH  = str(ROOT_DIR / "vector_store")    # 벡터DB 로컬 저장 경로
COLLECTION_NAME = "skin_knowledge_base"
BATCH_SIZE = 500

# ─────────────────────────────────────────────────────────────
# DB 연결
# ─────────────────────────────────────────────────────────────

def get_collection(db_path: str, collection_name: str):
    try:
        client = chromadb.PersistentClient(path=db_path)
    except Exception as e:
        print(f"[ERROR] DB 연결 실패: {e}\n        경로 확인: {db_path}")
        
        return None, None

    collections = client.list_collections()

    print(f"\n{'='*55}")
    print(f"  DB 경로: {db_path}")
    print(f"  전체 컬렉션 수: {len(collections)}개")

    for c in collections:
        marker = " ◀ 현재 대상" if c.name == collection_name else ""
        print(f"    - {c.name}{marker}")

    print(f"{'='*55}")

    try:
        col = client.get_collection(name=collection_name)
        return client, col
    except Exception:
        print(f"\n[ERROR] 컬렉션 '{collection_name}'을 찾을 수 없습니다.")
        print(f"        --collection 옵션으로 이름을 지정해주세요.")
        return client, None


# ─────────────────────────────────────────────────────────────
# 전체 통계 (기본 모드)
# ─────────────────────────────────────────────────────────────

def cmd_stats(col) -> None:
    """옵션 없이 실행 시 전체 통계 출력"""
    total   = col.count()
    fetch_n = min(total, 50000)

    print(f"\n  컬렉션: {col.name}")
    print(f"  총 문서 수: {total:,}개\n")

    if total == 0:
        print("  저장된 문서가 없습니다.")
        return

    metas = []
    offset = 0

    while offset < fetch_n:
        batch = col.get(limit=min(BATCH_SIZE, fetch_n - offset),
                        offset=offset,
                        include=["metadatas"])
        metas.extend(batch["metadatas"])
        offset += BATCH_SIZE

        if len(batch["metadatas"]) < BATCH_SIZE:
            break

    doc_types    = Counter(m.get("doc_type", "unknown") for m in metas)
    categories   = Counter(m.get("category", "unknown") for m in metas)
    sources      = Counter(m.get("source",   "unknown") for m in metas)
    skin_types   = Counter()
    concern_tags = Counter()

    for m in metas:
        for st in m.get("skin_type",   "").split(","):
            if st.strip():
                skin_types[st.strip()] += 1
        for ct in m.get("concern_tag", "").split(","):
            if ct.strip():
                concern_tags[ct.strip()] += 1

    def print_counter(title: str, counter: Counter, top: int = 10) -> None:
        print(f"  [{title}]")
        if not counter:
            print("    (없음)")
            print()
            return
        max_val = max(counter.values())
        for key, cnt in counter.most_common(top):
            bar = "█" * int(cnt / max_val * 20)
            print(f"    {key:<28} {cnt:>6,}개  {bar}")
        print()

    print_counter("문서 유형 (doc_type)",  doc_types)
    print_counter("카테고리 (category)",   categories)
    print_counter("출처 (source)",         sources)
    print_counter("피부 타입 (skin_type)", skin_types)
    print_counter("피부 고민 태그",        concern_tags)

    if fetch_n < total:
        print(f"  ※ 통계는 상위 {fetch_n:,}건 샘플 기준 (전체 {total:,}건)\n")

    print(f"{'='*55}\n")


# ─────────────────────────────────────────────────────────────
# source 분포 + ID 샘플 (--list-sources)
# ─────────────────────────────────────────────────────────────

def cmd_list_sources(col) -> None:
    """전체 source 분포와 ID 샘플 출력"""
    total   = col.count()
    fetch_n = min(total, 50000)
    
    metas, ids = [], []
    offset = 0

    while offset < fetch_n:
        batch = col.get(limit=min(BATCH_SIZE, fetch_n - offset),
                        offset=offset,
                        include=["metadatas"])
        metas.extend(batch["metadatas"])
        ids.extend(batch["ids"])
        offset += BATCH_SIZE

        if len(batch["metadatas"]) < BATCH_SIZE:
            break

    sources   = Counter(m.get("source",   "(없음)") for m in metas)
    doc_types = Counter(m.get("doc_type", "(없음)") for m in metas)

    print(f"\n  총 {total:,}건\n")

    print("  [source 전체 분포]")
    for src, cnt in sources.most_common():
        print(f"    {src:<35} {cnt:>6,}건")

    print("\n  [doc_type 전체 분포]")
    for dt, cnt in doc_types.most_common():
        print(f"    {dt:<25} {cnt:>6,}건")

    print(f"\n  [저장된 ID 샘플 (앞 20개)]")
    for id_ in ids[:20]:
        print(f"    {id_}")

    print(f"\n{'='*55}\n")


# ─────────────────────────────────────────────────────────────
# source 필터 조회 (--source)
# ─────────────────────────────────────────────────────────────

def cmd_source(col, source: str, limit: int) -> None:
    print(f"\n  [source = '{source}'] 조회 중...\n")
    try:
        results = col.get(
            where={"source": {"$eq": source}},
            limit=limit,
            include=["metadatas", "documents"],
        )
    except Exception as e:
        print(f"  [ERROR] 조회 실패: {e}")
        return

    ids, metas, docs = results["ids"], results["metadatas"], results["documents"]

    if not ids:
        print(f"  source='{source}' 인 데이터가 없습니다.")
        print("\n  → 저장된 source 목록 확인:")
        print("    python check_collection.py --list-sources")
        return

    print(f"  {len(ids)}건 조회됨 (limit={limit})\n")
    _print_docs(ids, metas, docs)


# ─────────────────────────────────────────────────────────────
# id 접두어 조회 (--id-prefix)
# ─────────────────────────────────────────────────────────────

def cmd_id_prefix(col, prefix: str, limit: int) -> None:
    print(f"\n  [id prefix = '{prefix}'] 조회 중...\n")

    total   = col.count()
    ids, metas, docs = [], [], []
    offset = 0

    while offset < total:
        batch = col.get(limit=min(BATCH_SIZE, total - offset),
                        offset=offset,
                        include=["metadatas", "documents"])
        ids.extend(batch["ids"])
        metas.extend(batch["metadatas"])
        docs.extend(batch["documents"])
        offset += BATCH_SIZE

        if len(batch["ids"]) < BATCH_SIZE:
            break

    matched = [(ids[i], metas[i], docs[i]) for i, id_ in enumerate(ids) if id_.startswith(prefix)]

    if not matched:
        print(f"  id가 '{prefix}'로 시작하는 데이터가 없습니다.")
        print("\n  저장된 ID 샘플:")
        for id_ in ids[:15]:
            print(f"    {id_}")
        return

    print(f"  {len(matched)}건 매칭 (limit={limit} 출력)\n")
    m_ids, m_metas, m_docs = zip(*matched[:limit])
    _print_docs(list(m_ids), list(m_metas), list(m_docs))

    if len(matched) > limit:
        print(f"  ... 외 {len(matched) - limit}건 더 있음")


# ─────────────────────────────────────────────────────────────
# doc_type 필터 조회 (--doc-type)
# ─────────────────────────────────────────────────────────────

def cmd_doc_type(col, doc_type: str, limit: int) -> None:
    print(f"\n  [doc_type = '{doc_type}'] 조회 중...\n")
    try:
        results = col.get(
            where={"doc_type": {"$eq": doc_type}},
            limit=limit,
            include=["metadatas", "documents"],
        )
    except Exception as e:
        print(f"  [ERROR] 조회 실패: {e}")
        return

    ids, metas, docs = results["ids"], results["metadatas"], results["documents"]

    if not ids:
        print(f"  doc_type='{doc_type}' 인 데이터가 없습니다.")
        return

    print(f"  {len(ids)}건 조회됨 (limit={limit})\n")
    _print_docs(ids, metas, docs)


# ─────────────────────────────────────────────────────────────
# 공통 출력 유틸
# ─────────────────────────────────────────────────────────────

def _print_docs(ids, metas, docs) -> None:
    for i, (id_, meta, doc) in enumerate(zip(ids, metas, docs), 1):
        print(f"  ── [{i}] " + "─" * 42)
        print(f"  ID          : {id_}")
        print(f"  doc_type    : {meta.get('doc_type',    '-')}")
        print(f"  category    : {meta.get('category',    '-')}")
        print(f"  skin_type   : {meta.get('skin_type',   '-')}")
        print(f"  concern_tag : {meta.get('concern_tag', '-')}")
        print(f"  source      : {meta.get('source',      '-')}")
        print(f"  content     : {doc[:150].replace(chr(10), ' ')}...")
        print()

# ─────────────────────────────────────────────────────────────
# source 삭제 (--delete-source)
# ─────────────────────────────────────────────────────────────

def cmd_delete_source(col, source: str) -> None:
    """특정 source의 문서를 전부 삭제"""

    # 1. 삭제 대상 ID 조회
    print(f"\n  [source = '{source}'] 삭제 대상 조회 중...")

    total = col.count()
    ids, metas = [], []
    offset = 0

    while offset < total:
        batch = col.get(limit=min(BATCH_SIZE, total - offset), offset=offset, include=["metadatas"])
        ids.extend(batch["ids"])
        metas.extend(batch["metadatas"])
        offset += BATCH_SIZE

        if len(batch["ids"]) < BATCH_SIZE:
            break

    target_ids = [id_ for id_, m in zip(ids, metas) if m.get("source") == source]

    if not target_ids:
        print(f"  source='{source}' 인 데이터가 없습니다.")
        print("\n  저장된 source 목록 확인:")
        print("    python check_collection.py --list-sources")

        return

    print(f"  삭제 대상: {len(target_ids):,}건")
    print(f"  삭제 후 예상 잔여: {total - len(target_ids):,}건")

    # 2. 확인 프롬프트
    answer = input(f"\n  정말 삭제하시겠습니까? (yes 입력 시 삭제): ").strip().lower()

    if answer != "yes":
        print("  삭제 취소됨.")
        return

    # 3. 배치 삭제 (ChromaDB는 한 번에 대량 삭제 시 느릴 수 있어 배치 처리)
    BATCH = 500
    deleted = 0
    
    for start in range(0, len(target_ids), BATCH):
        batch = target_ids[start:start + BATCH]
        col.delete(ids=batch)
        deleted += len(batch)
        print(f"  삭제 중... {deleted}/{len(target_ids)}건", end="\r")

    print(f"\n  ✓ 삭제 완료: {deleted:,}건")
    print(f"  현재 컬렉션 총 문서 수: {col.count():,}건\n")

# ─────────────────────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ChromaDB 컬렉션 통계 확인 & 데이터 조회",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db-path",      default=DB_PATH,         help=f"벡터DB 경로 (기본: {DB_PATH})")
    parser.add_argument("--collection",   default=COLLECTION_NAME, help=f"컬렉션 이름 (기본: {COLLECTION_NAME})")
    parser.add_argument("--list-sources", action="store_true",     help="전체 source 분포 + ID 샘플 출력")
    parser.add_argument("--source",       default=None,            help="source 값으로 필터 (예: derma_kr)")
    parser.add_argument("--id-prefix",    default=None,            help="id 접두어로 필터 (예: derma_disease)")
    parser.add_argument("--doc-type",     default=None,            help="doc_type으로 필터 (guide / ingredient)")
    parser.add_argument("--delete-source", default=None,            help="해당 source 문서 전체 삭제 (예: aad_org)")
    parser.add_argument("--limit",        type=int, default=5,     help="조회 시 출력할 최대 건수 (기본: 5)")
    args = parser.parse_args()

    _, col = get_collection(args.db_path, args.collection)

    if col is None:
        return

    if args.delete_source:
        cmd_delete_source(col, args.delete_source)
    elif args.list_sources:
        cmd_list_sources(col)
    elif args.source:
        cmd_source(col, args.source, args.limit)
    elif args.id_prefix:
        cmd_id_prefix(col, args.id_prefix, args.limit)
    elif args.doc_type:
        cmd_doc_type(col, args.doc_type, args.limit)
    else:
        cmd_stats(col)   # 기본: 전체 통계


if __name__ == "__main__":
    main()