"""
식품의약품안전처_기능성화장품 보고품목정보 API → 벡터DB JSON 변환 스크립트
=============================================================================
공공데이터포털: https://www.data.go.kr/data/15095680/openapi.do

수집 필드 (벡터화 대상):
    - ITEM_NAME           : 품목명
    - EE_NAME             : 효능효과명
    - EE_DOC_DATA         : 효능효과 문서 (상세)
    - USAGE_DOSAGE        : 용법용량
    - UD_DOC_DATA         : 용법용량 문서 (상세)
    - NB_DOC_DATA         : 주의사항(일반) 문서

메타데이터 필드:
    - COSMETIC_REPORT_SEQ : 화장품보고일련번호 (고유 ID)
    - REPORT_FLAG_NAME    : 화장품보고구분명 (제조/수입)
    - MANUF_COUNTRY_NAME  : 제조국가명
    - COSMETIC_STD_NAME   : 화장품기준명
    - COSMETIC_TARGET_FLAG_NAME : 화장품대상구분명
    - SPF / PA            : 자외선차단지수
    - WATER_PROOFING_NAME : 내수성 여부
    - CANCEL_APPROVAL_YN  : 취하승인여부 (Y → 수집 제외)
    - EFFECT_YN1/2/3      : 미백 / 주름개선 / 자외선차단 효능 여부
    - ENTP_NAME           : 업소명

출력 포맷 (vectordb_insert.py 호환):
    - id, doc_type, category, skin_type, concern_tag, ingredient_tag, source, chunk_index, content
    + 기능성화장품 전용 메타 필드

출력 파일:
    - OUTPUT_DIR/mfds_cosmetic_report.json

사용법:
    python cosmetic_report_to_json.py
    python cosmetic_report_to_json.py --max-pages 10
    python cosmetic_report_to_json.py --item-name "선크림"
    python cosmetic_report_to_json.py --effect whitening     # 미백 제품만
    python cosmetic_report_to_json.py --effect antiaging     # 주름개선 제품만
    python cosmetic_report_to_json.py --effect suncare       # 자외선차단 제품만
    python cosmetic_report_to_json.py --output-dir ./assets/vector_data

필터 옵션:
    --effect  : whitening / antiaging / suncare / all (기본: all)
    --exclude-cancelled : 취하 제품 제외 (기본: True)

주의:
    - DATA_GO_COSMETIC_REPORT_KEY 환경 변수에 API 키 설정 필요
    - 취하 승인된 제품(CANCEL_APPROVAL_YN=Y)은 기본 제외
    - EE_DOC_DATA 등 대용량 문서 필드는 청크 분할하여 저장
    - 문서 필드가 없는 경우 단문 필드(EE_NAME 등)로 대체
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
from utils.tagging import (CATEGORY_RULES, SKIN_TYPE_RULES, CONCERN_TAG_RULES, INGREDIENT_TAG_RULES, match_tags)

load_dotenv()

# ─────────────────────────────────────────────────────────────
# [설정]
# ─────────────────────────────────────────────────────────────
BASE_URL          = "http://apis.data.go.kr/1471000/FtnltCosmRptPrdlstInfoService/getRptPrdlstInq"
API_KEY           = os.getenv("DATA_GO_COSMETIC_KEY")
OUTPUT_DIR        = Path("./assets/vector_data")
OUTPUT_FILE       = "mfds_cosmetic_report.jsonl"
DEFAULT_PAGE_SIZE = 100       # 1회 호출 건수 (최대 100)
REQUEST_DELAY     = 0.35      # 요청 간 딜레이 (초)
CHUNK_MAX_CHARS   = 1000      # 대용량 문서 필드 1청크 최대 글자 수
EFFECT_FILTER_MAP = {
    "whitening": {"EFFECT_YN1": "Y"},   # 미백
    "antiaging": {"EFFECT_YN2": "Y"},   # 주름개선
    "suncare":   {"EFFECT_YN3": "Y"},   # 자외선차단
    "all":       {},
}
# 제품구분을 위한 EFFECT_FILTER_MAP
HAIR_TARGET_FLAGS = {   # (필드명: COSMETIC_TARGET_FLAG_NAME)
    "제2조 제6호",   # 염모
    "제2조 제7호",   # 제모
    "제2조 제8호",   # 탈모
}
HAIR_KEYWORDS = ["두피", "모발", "모근", "탈모", "샴푸", "헤어", "염모", "제모", "hair", "scalp", "shampoo", "alopecia"]

# [유틸]

def safe_get(item: dict, key: str) -> str:
    """None 포함 가능한 필드를 안전하게 문자열로 반환"""
    return (item.get(key) or "").strip()


def is_cancelled(item: dict) -> bool:
    """취하 승인 여부 확인 (Y = 취하됨 → 제외)"""
    return safe_get(item, "CANCEL_APPROVAL_YN").upper() == "Y"

def is_face_product(item: dict) -> bool:
    target_flag = safe_get(item, "COSMETIC_TARGET_FLAG_NAME")

    target_flag_normalized = target_flag.replace(" ", "")
    if any(flag.replace(" ", "") in target_flag_normalized for flag in HAIR_TARGET_FLAGS):
        return False

    check_text = " ".join([
        safe_get(item, "ITEM_NAME"),
        safe_get(item, "EE_NAME"),
        safe_get(item, "EE_DOC_DATA")[:500] if safe_get(item, "EE_DOC_DATA") else "",
        safe_get(item, "NB_DOC_DATA")[:500] if safe_get(item, "NB_DOC_DATA") else "",
    ]).lower()

    if any(kw.lower() in check_text for kw in HAIR_KEYWORDS):
        return False

    return True

def split_chunks(text: str, max_chars: int = CHUNK_MAX_CHARS) -> list[str]:
    """
    긴 텍스트를 문장 경계 기준으로 청크 분할.
    max_chars 이하인 경우 단일 청크로 반환.
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    chunks, buf = [], ""

    for sentence in text.replace("。", ".").split("."):
        sentence = sentence.strip()

        if not sentence:
            continue

        candidate = buf + ("." if buf else "") + sentence

        if len(candidate) > max_chars and buf:
            chunks.append(buf.strip())
            buf = sentence
        else:
            buf = candidate

    if buf.strip():
        chunks.append(buf.strip())

    return chunks if chunks else [text[:max_chars]]

# content 생성
def build_content_text(item: dict) -> str:
    """
    API 응답 필드 → 임베딩용 content 텍스트 생성.

    우선순위:
        1) 대용량 문서 필드 (EE_DOC_DATA, UD_DOC_DATA, NB_DOC_DATA) 사용
        2) 없으면 단문 필드 (EE_NAME, USAGE_DOSAGE) 로 대체

    항상 [제품명], [효능효과], [용법용량], [주의사항] 섹션 포함.
    """
    item_name  = safe_get(item, "ITEM_NAME")
    entp_name  = safe_get(item, "ENTP_NAME")

    # 효능효과: 문서 우선, 없으면 단문
    ee_text = safe_get(item, "EE_DOC_DATA") or safe_get(item, "EE_NAME")

    # 용법용량: 문서 우선, 없으면 단문
    ud_text = safe_get(item, "UD_DOC_DATA") or safe_get(item, "USAGE_DOSAGE")

    # 주의사항: 문서 필드만 존재
    nb_text = safe_get(item, "NB_DOC_DATA")

    # SPF / PA / 내수성 보조 정보
    spf           = safe_get(item, "SPF")
    pa            = safe_get(item, "PA")
    water_proof   = safe_get(item, "WATER_PROOFING_NAME")
    cosmetic_std  = safe_get(item, "COSMETIC_STD_NAME")
    manuf_country = safe_get(item, "MANUF_COUNTRY_NAME")

    lines = []

    if item_name:
        lines.append(f"[제품명] {item_name}")
    if entp_name:
        lines.append(f"[제조·판매사] {entp_name}")
    if cosmetic_std:
        lines.append(f"[기준] {cosmetic_std}")
    if manuf_country:
        lines.append(f"[제조국] {manuf_country}")
    if ee_text:
        lines.append(f"[효능효과] {ee_text}")
    if ud_text:
        lines.append(f"[용법용량] {ud_text}")
    if nb_text:
        lines.append(f"[주의사항] {nb_text}")

    # 자외선차단 관련 수치 추가
    sun_info_parts = []
    if spf:
        sun_info_parts.append(f"SPF {spf}")
    if pa:
        sun_info_parts.append(f"PA {pa}")
    if water_proof:
        sun_info_parts.append(f"내수성: {water_proof}")
    if sun_info_parts:
        lines.append(f"[자외선차단정보] {', '.join(sun_info_parts)}")

    return "\n".join(lines)

# 태깅 보조: 효능 YN 필드 → concern_tag 매핑
EFFECT_YN_TO_CONCERN = {
    "EFFECT_YN1": "brightening",    # 미백
    "EFFECT_YN2": "anti-aging",     # 주름개선
    "EFFECT_YN3": "suncare",        # 자외선차단
}

def build_concern_tags(item: dict, text_based: list[str]) -> list[str]:
    """
    텍스트 기반 태그 + EFFECT_YN 플래그 기반 태그를 합산 (중복 제거).
    """
    flag_tags = [
        tag
        for field, tag in EFFECT_YN_TO_CONCERN.items()
        if safe_get(item, field).upper() == "Y"
    ]

    return list(dict.fromkeys(text_based + flag_tags))


def build_ingredient_tags(item: dict, text_based: list[str]) -> list[str]:
    """
    텍스트 기반 성분 태그 + SPF 여부로 sunscreen 태그 보완.
    """
    extra = []

    if safe_get(item, "SPF"):
        extra.append("sunscreen")

    return list(dict.fromkeys(text_based + extra))

# 단건 변환
def transform(item: dict, seq_no: int) -> list[dict]:
    """
    API raw 응답 단건 → vectordb_insert.py JSON 포맷 (1건 이상 반환 가능).

    대용량 문서 필드(EE_DOC_DATA 등)가 CHUNK_MAX_CHARS 초과 시
    청크 분할하여 복수 문서로 반환.
    """
    report_seq = safe_get(item, "COSMETIC_REPORT_SEQ") or f"seq{seq_no:06d}"
    item_name  = safe_get(item, "ITEM_NAME")

    # 분류 텍스트 (태깅용)
    classify_text = " ".join(filter(None, [
        item_name,
        safe_get(item, "EE_NAME"),
        safe_get(item, "EE_DOC_DATA")[:500] if safe_get(item, "EE_DOC_DATA") else "",
        safe_get(item, "NB_DOC_DATA")[:300] if safe_get(item, "NB_DOC_DATA") else "",
    ]))

    # 태깅
    category        = (match_tags(classify_text, CATEGORY_RULES) or ["general"])[0]
    skin_type       = match_tags(classify_text, SKIN_TYPE_RULES)
    concern_tags_tx = match_tags(classify_text, CONCERN_TAG_RULES)
    ingr_tags_tx    = match_tags(classify_text, INGREDIENT_TAG_RULES)

    concern_tag    = build_concern_tags(item, concern_tags_tx)
    ingredient_tag = build_ingredient_tags(item, ingr_tags_tx)

    # 공통 메타데이터
    meta = {
        "doc_type":       "cosmetic_product",
        "category":       category,
        "skin_type":      skin_type,
        "concern_tag":    concern_tag,
        "ingredient_tag": ingredient_tag,
        "source":         "mfds_cosmetic_report_api",
        # ── 기능성화장품 전용 메타 ──
        "item_name":              item_name,
        "entp_name":              safe_get(item, "ENTP_NAME"),
        "report_type":            safe_get(item, "REPORT_FLAG_NAME"),
        "manuf_country":          safe_get(item, "MANUF_COUNTRY_NAME"),
        "cosmetic_std":           safe_get(item, "COSMETIC_STD_NAME"),
        "target_type":            safe_get(item, "COSMETIC_TARGET_FLAG_NAME"),
        "spf":                    safe_get(item, "SPF"),
        "pa":                     safe_get(item, "PA"),
        "water_proof":            safe_get(item, "WATER_PROOFING_NAME"),
        "effect_whitening":       safe_get(item, "EFFECT_YN1"),
        "effect_antiaging":       safe_get(item, "EFFECT_YN2"),
        "effect_suncare":         safe_get(item, "EFFECT_YN3"),
        "cancel_yn":              safe_get(item, "CANCEL_APPROVAL_YN"),
    }

    # content 생성 및 청크 분할
    full_content = build_content_text(item)
    chunks       = split_chunks(full_content, CHUNK_MAX_CHARS)

    if not chunks:
        chunks = [f"[제품명] {item_name}"]  # fallback

    docs = []

    for chunk_idx, chunk_text in enumerate(chunks):
        docs.append({
            "id":          f"mfds_crpt_{report_seq}_{chunk_idx:02d}",
            **meta,
            "chunk_index": chunk_idx,
            "content":     chunk_text,
        })

    return docs

# API 호출
def fetch_page(service_key: str, page_no: int, num_of_rows: int, item_name: str = "", effect_params: dict = None) -> dict:
    """API 1페이지 호출 → {"total": int, "items": list}"""
    params = {
        "serviceKey": service_key,
        "pageNo":     page_no,
        "numOfRows":  num_of_rows,
        "type":       "json",
    }

    if item_name:
        params["ITEM_NAME"] = item_name

    if effect_params:
        params.update(effect_params)

    try:
        resp = requests.get(BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] 요청 실패 (page {page_no}): {e}")

        return {"total": 0, "items": []}

    try:
        data = resp.json()
        body = data.get("body", {})

        total = int(body.get("totalCount", 0))
        items = body.get("items", [])

        # 단건 응답이 dict로 오는 경우 처리
        if isinstance(items, dict):
            items = [items] if items else []

        return {"total": total, "items": items}

    except (KeyError, TypeError, json.JSONDecodeError) as e:
        print(f"  [ERROR] 응답 파싱 실패 (page {page_no}): {e}")
        print(f"  응답 미리보기: {resp.text[:300]}")

        return {"total": 0, "items": []}

# 전체 수집 (제너레이터)
def iter_all(service_key: str, page_size: int, max_pages: int, item_name: str, effect: str, exclude_cancelled: bool):
    """전 페이지 순회 수집 → 변환된 JSON 문서를 yield하는 제너레이터"""
    effect_params = EFFECT_FILTER_MAP.get(effect, {})

    print(f"\n{'='*55}")
    print(f"  식약처 기능성화장품 보고품목정보 수집 시작")

    if item_name:
        print(f"  품목명 필터: {item_name}")

    print(f"  효능 필터:   {effect} {effect_params if effect_params else '(전체)'}")
    print(f"  취하 제외:   {exclude_cancelled}")
    print(f"{'='*55}\n")

    # 1페이지 → totalCount 확인
    first = fetch_page(service_key, 1, page_size, item_name, effect_params)

    if first["total"] == 0:
        print("  [ERROR] 데이터 없음. API 키 또는 파라미터를 확인하세요.")
        return

    total_count = first["total"]
    total_pages = math.ceil(total_count / page_size)

    if max_pages > 0:
        total_pages = min(total_pages, max_pages)

    print(f"  총 데이터: {total_count:,}건 → {total_pages}페이지 수집 예정\n")

    yielded_cnt   = 0
    cancelled_cnt = 0
    hair_cnt      = 0
    seq_counter   = 1

    def _process_page(items: list):
        nonlocal yielded_cnt, cancelled_cnt, hair_cnt, seq_counter

        for item in items:
            if exclude_cancelled and is_cancelled(item):
                cancelled_cnt += 1
                continue

            if not is_face_product(item):
                hair_cnt += 1
                continue

            for doc in transform(item, seq_counter):
                yield doc
                yielded_cnt += 1

            seq_counter += 1

    yield from _process_page(first["items"])
    print(f"  page  1 / {total_pages}  ({yielded_cnt:,}건 누적, 취하제외 {cancelled_cnt} | 두피·모발제외 {hair_cnt})")

    for page_no in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY)
        result = fetch_page(service_key, page_no, page_size, item_name, effect_params)
        yield from _process_page(result["items"])
        print(f"  page {page_no:>2} / {total_pages}  ({yielded_cnt:,}건 누적, 취하제외 {cancelled_cnt} | 두피·모발제외 {hair_cnt})")

    print(f"\n  수집 완료: {yielded_cnt:,}건")
    print(f"  제외 현황: 취하 {cancelled_cnt}건 / 두피·모발 {hair_cnt}건")

# JSONL 저장 (제너레이터 입력)
def save_jsonl(docs_iter, output_dir: Path, sample_n: int = 0) -> tuple[Path, int, list[dict]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / OUTPUT_FILE
    count, sample = 0, []

    with open(file_path, "w", encoding="utf-8") as f:
        for doc in docs_iter:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1
            if sample_n and len(sample) < sample_n:
                sample.append(doc)

    print(f"\n[저장 완료]")
    print(f"  경로: {file_path}")
    print(f"  건수: {count:,}건")
    print(f"  크기: {file_path.stat().st_size / 1024:.1f} KB\n")

    return file_path, count, sample

# 저장 샘플 출력
def print_sample(items: list[dict], n: int = 2) -> None:
    print(f"\n[샘플 출력 (상위 {n}건)]")

    for doc in items[:n]:
        print(f"\n  id            : {doc['id']}")
        print(f"  item_name     : {doc['item_name']}")
        print(f"  doc_type      : {doc['doc_type']}")
        print(f"  category      : {doc['category']}")
        print(f"  skin_type     : {doc['skin_type']}")
        print(f"  concern_tag   : {doc['concern_tag']}")
        print(f"  ingredient_tag: {doc['ingredient_tag']}")
        print(f"  effect_flags  : 미백={doc['effect_whitening']} / 주름={doc['effect_antiaging']} / 자외선={doc['effect_suncare']}")
        print(f"  spf/pa        : SPF {doc['spf']} / PA {doc['pa']}")
        print(f"  chunk_index   : {doc['chunk_index']}")
        print(f"  content 미리보기:\n    {doc['content'][:120]}...")
    print()

# 메인 함수
def main():
    parser = argparse.ArgumentParser(description="식약처 기능성화장품 보고품목정보 API → 벡터DB JSON 변환")
    parser.add_argument(
        "--page-size", type=int, default=DEFAULT_PAGE_SIZE,
        help=f"페이지당 수집 건수 (기본: {DEFAULT_PAGE_SIZE}, 최대: 100)"
    )
    parser.add_argument(
        "--max-pages", type=int, default=0,
        help="최대 수집 페이지 수 (기본: 0 = 전체)"
    )
    parser.add_argument(
        "--item-name", default="",
        help="품목명 검색 필터 (예: '선크림', '미백')"
    )
    parser.add_argument(
        "--effect",
        choices=["whitening", "antiaging", "suncare", "all"],
        default="all",
        help="효능 필터 (기본: all)"
    )
    parser.add_argument(
        "--no-exclude-cancelled", action="store_true",
        help="취하 제품도 포함 (기본: 취하 제품 제외)"
    )
    parser.add_argument(
        "--output-dir", default=str(OUTPUT_DIR),
        help=f"저장 경로 (기본: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--sample", action="store_true",
        help="수집 후 샘플 출력"
    )
    args = parser.parse_args()

    if not API_KEY:
        print("[ERROR] API 키가 설정되지 않았습니다.")
        print("  .env 파일에 DATA_GO_COSMETIC_KEY=<인증키> 를 추가하세요.")

        return

    docs_iter = iter_all(
        service_key        = API_KEY,
        page_size          = args.page_size,
        max_pages          = args.max_pages,
        item_name          = args.item_name,
        effect             = args.effect,
        exclude_cancelled  = not args.no_exclude_cancelled,
    )

    _, count, sample = save_jsonl(docs_iter, Path(args.output_dir), sample_n=2 if args.sample else 0)

    if count == 0:
        print("  수집된 데이터가 없습니다.")
        return

    if args.sample and sample:
        print_sample(sample)

if __name__ == "__main__":
    main()