"""
식품의약품안전처_화장품 원료성분정보 API 수집 스크립트
======================================================
공공데이터포털: https://www.data.go.kr/data/15111774/openapi.do

수집 필드:
  - INGR_KOR_NAME           : 성분 표준명 (한글)
  - INGR_ENG_NAME           : 영문명
  - CAS_NO                  : CAS No
  - ORIGIN_MAJOR_KOR_NAME   : 기원 및 정의
  - INGR_SYNONYM            : 이명

출력 포맷 (vectordb_insert.py 호환):
  - id, doc_type, category, skin_type, concern_tag,
    ingredient_tag, source, chunk_index, content

출력 파일:
  - OUTPUT_DIR/mfds_ingredients.json

사용법:
  python collect_mfds_ingredients.py
  python collect_mfds_ingredients.py --max-pages 5
  python collect_mfds_ingredients.py --name "세라마이드"
"""

import os
import sys
import json
import time
import math
import argparse
import requests

from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.tagging import (CATEGORY_RULES, SKIN_TYPE_RULES, CONCERN_TAG_RULES, match_tags)

load_dotenv()

# [설정]

BASE_URL          = "https://apis.data.go.kr/1471000/CsmtcsIngdCpntInfoService01/getCsmtcsIngdCpntInfoService01"
API_KEY           = os.getenv('DATA_GO_CSMT_KEY')
OUTPUT_DIR        = Path("./assets/vector_data")
DEFAULT_PAGE_SIZE = 100    # 1회 호출 건수 (최대 100)
REQUEST_DELAY     = 0.3    # 요청 간 딜레이 (초)


def safe_get(item: dict, key: str) -> str:
    """None 포함 가능한 필드를 안전하게 문자열로 반환"""
    
    return (item.get(key) or "").strip()

def build_content(item: dict) -> str:
    """API 응답 필드 → content 텍스트 생성"""
    fields = [
        ("성분명(한글)", safe_get(item, "INGR_KOR_NAME")),
        ("성분명(영문)", safe_get(item, "INGR_ENG_NAME")),
        ("CAS No",      safe_get(item, "CAS_NO")),
        ("이명",         safe_get(item, "INGR_SYNONYM")),
        ("기원 및 정의", safe_get(item, "ORIGIN_MAJOR_KOR_NAME")),
    ]

    return "\n".join(f"{k}: {v}" for k, v in fields if v)

def transform(item: dict, seq_no: int) -> dict:
    """API raw 응답 단건 → vectordb_insert.py JSON 포맷"""
    name_ko = safe_get(item, "INGR_KOR_NAME")
    name_en = safe_get(item, "INGR_ENG_NAME")
    origin  = safe_get(item, "ORIGIN_MAJOR_KOR_NAME")

    classify_text = f"{name_ko} {name_en} {origin}"

    matched_categories = match_tags(classify_text, CATEGORY_RULES)
    category           = matched_categories[0] if matched_categories else "general"

    ingredient_tags = [t for t in [name_ko, name_en.lower()] if t]

    return {
        "id":             f"mfds_ingd_{seq_no:06d}",
        "doc_type":      "ingredient",
        "category":       category,
        "skin_type":      match_tags(classify_text, SKIN_TYPE_RULES),
        "concern_tag":    match_tags(classify_text, CONCERN_TAG_RULES),
        "ingredient_tag": ingredient_tags,
        "source":         "mfds_ingredient_api",
        "chunk_index":    0,
        "content":        build_content(item),
    }

# API 호출
def fetch_page(service_key: str, page_no: int, num_of_rows: int, ingd_name: str = "") -> dict:
    """API 1페이지 호출 → {"total": int, "items": list}"""

    params = {
        "serviceKey": service_key,
        "pageNo":     page_no,
        "numOfRows":  num_of_rows,
        "type":       "json",
    }

    if ingd_name:
        params["INGR_KOR_NAME"] = ingd_name

    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 요청 실패 (page {page_no}): {e}")
        return {"total": 0, "items": []}

    try:
        data  = resp.json()
        body  = data["body"]
        total = int(body.get("totalCount", 0))
        items = body.get("items", [])

        # 단건 응답이 dict로 오는 경우 처리
        if isinstance(items, dict):
            items = [items] if items else []

        return {"total": total, "items": items}

    except (KeyError, TypeError, json.JSONDecodeError) as e:
        print(f"  [ERROR] 응답 파싱 실패 (page {page_no}): {e}")
        print(f"  응답 미리보기: {resp.text[:200]}")

        return {"total": 0, "items": []}

# 전체 수집 (제너레이터)
def iter_all(service_key: str, page_size: int, max_pages: int, ingd_name: str):
    """전 페이지 순회 수집 → 변환된 JSON 문서를 yield하는 제너레이터"""

    print(f"\n{'='*50}")
    print(f"  식약처 화장품 원료성분정보 수집 시작")

    if ingd_name:
        print(f"  검색 성분: {ingd_name}")

    print(f"{'='*50}\n")

    # 1페이지 호출 → totalCount 확인
    first = fetch_page(service_key, 1, page_size, ingd_name)

    if first["total"] == 0:
        print("  [ERROR] 데이터 없음. API 키 또는 파라미터를 확인하세요.")
        return

    total_count = first["total"]
    total_pages = math.ceil(total_count / page_size)

    if max_pages > 0:
        total_pages = min(total_pages, max_pages)

    print(f"  총 데이터: {total_count:,}건 → {total_pages}페이지 수집 예정\n")

    yielded_cnt = 0
    seq_counter = 1

    for item in first["items"]:
        yield transform(item, seq_counter)
        seq_counter += 1
        yielded_cnt += 1

    print(f"  page  1 / {total_pages}  ({yielded_cnt:,}건 누적)")

    for page_no in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY)
        result = fetch_page(service_key, page_no, page_size, ingd_name)

        for item in result["items"]:
            yield transform(item, seq_counter)
            seq_counter += 1
            yielded_cnt += 1

        print(f"  page {page_no:>2} / {total_pages}  ({yielded_cnt:,}건 누적)")

    print(f"\n  수집 완료: {yielded_cnt:,}건")

# JSONL 저장 (제너레이터 입력)
def save_jsonl(docs_iter, output_dir: Path) -> tuple[Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "mfds_ingredients.jsonl"
    count = 0

    with open(file_path, "w", encoding="utf-8") as f:
        for doc in docs_iter:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1

    print(f"\n[저장 완료]")
    print(f"  경로: {file_path}")
    print(f"  건수: {count:,}건")
    print(f"  크기: {file_path.stat().st_size / 1024:.1f} KB\n")

    return file_path, count

# 메인 함수
def main():
    parser = argparse.ArgumentParser(description="식약처 화장품 원료성분정보 API 수집")
    parser.add_argument("--page-size",  type=int, default=DEFAULT_PAGE_SIZE, help="페이지당 수집 건수 (최대 100)")
    parser.add_argument("--max-pages",  type=int, default=0,      help="최대 페이지 수 (0 = 전체)")
    parser.add_argument("--name",       default="",               help="성분명 검색 필터 (예: 세라마이드)")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR),  help="저장 경로")
    args = parser.parse_args()

    docs_iter = iter_all(service_key=API_KEY, page_size=args.page_size, max_pages=args.max_pages, ingd_name=args.name)
    _, count = save_jsonl(docs_iter, Path(args.output_dir))

    if count == 0:
        print("  수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()