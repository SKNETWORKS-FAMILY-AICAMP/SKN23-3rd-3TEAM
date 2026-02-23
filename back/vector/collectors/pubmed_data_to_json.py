"""
PubMed E-utilities API → 벡터DB JSON 변환 스크립트
====================================================
PubMed API: https://www.ncbi.nlm.nih.gov/books/NBK25501/

수집 대상 카테고리:
    - 피부 타입별 관리
    - 피부 장벽 관리
    - 트러블/여드름 관리
    - 톤업/색소/미백 관리
    - 안티에이징(주름/탄력) 관련 관리
    - 민감 피부 진정 관리
    - 모공 관리
    - 피부 타입별 차이점
    - 성분 간 시너지/충돌 관계 (필수)
    - 주의/제한 성분 여부 및 이유 (필수)
    - 농도별 효과 차이 설명
    - 피부 타입별 적합성 설명

출력 포맷 (vectordb_insert.py 호환):
    - id, doc_type, category, skin_type, concern_tag, ingredient_tag, source, chunk_index, content

출력 파일:
    - OUTPUT_DIR/pubmed_skin_guides.json

사용법:
    python pubmed_data_to_json.py
    python pubmed_data_to_json.py --max-per-query 5
    python pubmed_data_to_json.py --output-dir ./assets/vector_data
    python pubmed_data_to_json.py --email your@email.com
    python pubmed_data_to_json.py --ncbi-key YOUR_NCBI_KEY
    python pubmed_data_to_json.py --openai-key YOUR_OPENAI_KEY
    python pubmed_data_to_json.py --no-translate          # 번역 생략 (영어 원문 저장)
    python pubmed_data_to_json.py --queries-file ./assets/links/queries.json

쿼리 JSON 파일 포맷 (문자열 배열):
    ["retinol interaction niacinamide skin", "살리실산 부작용", ...]
    - 영어/한글 혼용 가능
    - 한글이 포함된 항목은 GPT로 자동 영어 번역 후 검색
    - 파일 미지정 시 스크립트 내부 SEARCH_QUERIES 사용 (fallback)

주의:
    - NCBI API 키 없이도 동작 (속도 제한: 3 req/s → 키 보유 시 10 req/s)
    - NCBI API 키: https://www.ncbi.nlm.nih.gov/account/ 에서 무료 발급
    - 논문 전문은 저작권상 재배포 불가 → Abstract + 메타데이터 기반 요약 활용
    - GPT 번역은 .env 의 OPENAI_API_KEY 또는 --openai-key 인자로 활성화
    - 번역 모델: gpt-4o-mini (비용 최적, aad_data_to_json.py 와 동일 방식)
    - 구조 마커([주제], Title:, Authors:, [Abstract] 등)는 번역 후에도 유지됨
"""

import os
import json
import time
import argparse
import requests
import xml.etree.ElementTree as ET

from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from utils.tagging import (CATEGORY_RULES, SKIN_TYPE_RULES, CONCERN_TAG_RULES, INGREDIENT_TAG_RULES, match_tags)

load_dotenv()

# ─────────────────────────────────────────────────────────────
# [PubMed API 설정]
# ─────────────────────────────────────────────────────────────
ESEARCH_URL           = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL            = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

DEFAULT_QUERIES_FILE = Path("./assets/links/pubmed_queries.json")
OUTPUT_DIR            = Path("./assets/vector_data")
OUTPUT_FILE           = "pubmed_skin_guides.json"
DEFAULT_MAX_PER_QUERY = 10
DEFAULT_EMAIL         = os.getenv("PUBMED_EMAIL")
NCBI_API_KEY          = os.getenv("NCBI_API_KEY")
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
REQUEST_DELAY         = 0.11 if NCBI_API_KEY else 0.34  # 10 req/s vs 3 req/s

# ── GPT 번역 설정 (aad_data_to_json.py 와 동일 방식) ─────────────
GPT_MODEL         = "gpt-4o-mini"  # 번역 품질 대비 비용 최적 모델
GPT_MAX_CHARS     = 2000           # 청크 1개당 최대 글자 수 (초과 시 분할)
GPT_RETRY         = 2              # 번역 실패 시 재시도 횟수
GPT_RETRY_DELAY   = 3.0            # 재시도 대기 (초)
TRANSLATE_ENABLED = True           # --no-translate 플래그로 False 전환

# aad_data_to_json.py 와 동일한 구조 + PubMed 구조 마커 추가
TRANSLATE_SYSTEM_PROMPT = """You are a professional Korean medical translator specializing in dermatology and cosmetic science.
Translate the given English skin care / dermatology research text into natural Korean.

Rules:
- Translate only the actual content text
- Keep structural markers exactly as-is: "[주제]", "Title:", "Authors:", "Source:", "PMID:", "[Abstract]", "Keywords:", "MeSH:"
- Keep ingredient names, chemical names, brand names, and medical terms accurate
- Use formal Korean (합쇼체 아닌 해요체)
- Output only the translated text, no explanations"""

# [수집 쿼리 목록] ← 외부 파일 미사용 시 fallback
SEARCH_QUERIES = [
    # ── 피부 가이드 (guide) ──────────────────────────────────────
    {
        "query":    '"skin type" care routine review[Title/Abstract]',
        "doc_type": "guide",
        "category": "skin_type_care",
        "label":    "피부 타입별 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    '"skin barrier" function moisturizer review[Title/Abstract]',
        "doc_type": "guide",
        "category": "barrier",
        "label":    "피부 장벽 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    "acne vulgaris topical treatment management review[Title/Abstract]",
        "doc_type": "guide",
        "category": "acne",
        "label":    "트러블/여드름 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    "skin brightening whitening pigmentation treatment review[Title/Abstract]",
        "doc_type": "guide",
        "category": "pigmentation",
        "label":    "톤업/색소/미백 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    "anti-aging wrinkle elasticity skincare review[Title/Abstract]",
        "doc_type": "guide",
        "category": "anti-aging",
        "label":    "안티에이징(주름/탄력) 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    "sensitive skin soothing calming ingredient review[Title/Abstract]",
        "doc_type": "guide",
        "category": "sensitive",
        "label":    "민감 피부 진정 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    "pore size sebum skincare management review[Title/Abstract]",
        "doc_type": "guide",
        "category": "pore",
        "label":    "모공 관리",
        "filter":   "review[pt]",
    },
    {
        "query":    '"skin type" differences oily dry combination comparison[Title/Abstract]',
        "doc_type": "guide",
        "category": "skin_type_diff",
        "label":    "피부 타입별 차이점",
        "filter":   "review[pt]",
    },
    # ── 성분 정보 (ingredient) ────────────────────────────────────
    {
        "query":    "cosmetic ingredient synergy combination interaction skin[Title/Abstract]",
        "doc_type": "ingredient",
        "category": "ingredient_synergy",
        "label":    "성분 간 시너지/충돌 관계",
        "filter":   "review[pt]",
        "required": True,
    },
    {
        "query":    "cosmetic ingredient safety restriction irritation contraindication skin[Title/Abstract]",
        "doc_type": "ingredient",
        "category": "ingredient_caution",
        "label":    "주의/제한 성분 여부 및 이유",
        "filter":   "review[pt]",
        "required": True,
    },
    {
        "query":    "cosmetic ingredient concentration dose response efficacy skin[Title/Abstract]",
        "doc_type": "ingredient",
        "category": "ingredient_concentration",
        "label":    "농도별 효과 차이 설명",
        "filter":   "review[pt]",
    },
    {
        "query":    '"skin type" suitability cosmetic formulation ingredient[Title/Abstract]',
        "doc_type": "ingredient",
        "category": "ingredient_suitability",
        "label":    "피부 타입별 적합성 설명",
        "filter":   "review[pt]",
    },
]

# [외부 쿼리 파일 로드 + 한글→영어 변환]
def is_korean(text: str) -> bool:
    """텍스트에 한글이 포함되어 있는지 확인"""
    return any('\uAC00' <= ch <= '\uD7A3' or '\u1100' <= ch <= '\u11FF' for ch in text)

def translate_query_to_english(query: str, api_key: str) -> str:
    """
    한글 쿼리를 GPT로 영어 PubMed 검색어로 변환.
    실패 시 원문 반환.
    """
    if not api_key:
        print(f"    [WARN] OPENAI_API_KEY 없음 → 한글 쿼리 원문 사용: '{query}'")

        return query

    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": GPT_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a dermatology research assistant. "
                    "Translate the given Korean skin care query into a concise English PubMed search term. "
                    "Output only the English search term, no explanations."
                ),
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
    }

    for attempt in range(1, GPT_RETRY + 2):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            translated = resp.json()["choices"][0]["message"]["content"].strip()

            print(f"    [쿼리 번역] '{query}' → '{translated}'")

            return translated
        except requests.exceptions.RequestException as e:
            if attempt <= GPT_RETRY:
                print(f"    [쿼리 번역 재시도 {attempt}/{GPT_RETRY}] {e}")

                time.sleep(GPT_RETRY_DELAY)
            else:
                print(f"    [쿼리 번역 실패] 원문 사용: '{query}'")

                return query

def load_queries_from_file(file_path: Path, openai_key: str) -> list[dict]:
    """
    JSON 파일에서 쿼리 문자열 배열을 읽어 SEARCH_QUERIES 포맷으로 변환.

    입력 포맷: ["retinol interaction niacinamide skin", "살리실산 부작용", ...]

    출력 포맷 (SEARCH_QUERIES 호환): [{"query": "...", "label": "...", "doc_type": "ingredient", "category": "", "filter": "review[pt]"}, ...]

    - 한글 쿼리는 GPT로 영어 번역 후 사용
    - label 에 원본 쿼리(한글 포함) 저장 → content의 [주제] 필드에 반영
    """
    if not file_path.exists():
        raise FileNotFoundError(f"쿼리 파일을 찾을 수 없습니다: {file_path}")

    raw = json.loads(file_path.read_text(encoding="utf-8"))

    if not isinstance(raw, list) or not all(isinstance(q, str) for q in raw):
        raise ValueError("쿼리 파일은 문자열 배열 형식이어야 합니다. 예: [\"query1\", \"query2\"]")

    queries: list[dict] = []

    print(f"\n[쿼리 파일 로드] {file_path}  ({len(raw)}개)")

    for raw_query in raw:
        raw_query = raw_query.strip()

        if not raw_query:
            continue

        label = raw_query  # 원본(한글 포함)을 label로 보존

        # 한글 감지 → GPT로 영어 변환
        if is_korean(raw_query):
            eng_query = translate_query_to_english(raw_query, openai_key)
        else:
            eng_query = raw_query

        queries.append({
            "query":    eng_query,
            "label":    label,          # [주제] 필드에 원본 쿼리 표시
            "doc_type": "ingredient",   # 외부 쿼리 기본값
            "category": "",             # 태깅으로 자동 분류
            "filter":   "review[pt]",
        })

    print(f"  → {len(queries)}개 쿼리 준비 완료\n")

    return queries

def resolve_tags(text: str) -> dict:
    """텍스트 → 카테고리별 태그 딕셔너리 반환"""
    return {
        "category":       match_tags(text, CATEGORY_RULES),
        "skin_type":      match_tags(text, SKIN_TYPE_RULES),
        "concern_tag":    match_tags(text, CONCERN_TAG_RULES),
        "ingredient_tag": match_tags(text, INGREDIENT_TAG_RULES),
    }

# [GPT 번역] aad_data_to_json.py 와 동일한 방식
def _gpt_translate_chunk(text: str, api_key: str) -> Optional[str]:
    """
    텍스트 청크 1개를 GPT로 번역.
    실패 시 GPT_RETRY 횟수만큼 재시도 후 None 반환.
    """
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": GPT_MODEL,
        "messages": [
            {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
            {"role": "user",   "content": text},
        ],
        "temperature": 0.3,
    }

    for attempt in range(1, GPT_RETRY + 2):
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()

            return resp.json()["choices"][0]["message"]["content"].strip()

        except requests.exceptions.RequestException as e:
            if attempt <= GPT_RETRY:
                print(f"      [번역 재시도 {attempt}/{GPT_RETRY}] {e}")

                time.sleep(GPT_RETRY_DELAY)
            else:
                print(f"      [번역 실패] {e}")

                return None

def translate_content(content: str, api_key: str) -> str:
    """
    content 전체를 GPT로 한국어 번역.

    전략:
    - 구조 마커([주제], Title:, Authors: 등)는 프롬프트로 유지 지시
    - GPT_MAX_CHARS 초과 시 빈 줄 기준으로 청크 분할 → 순서대로 번역
    - 청크 단위 실패 시 해당 청크만 영어 원문으로 폴백
    """
    if not api_key:
        print("      [WARN] OPENAI_API_KEY 없음 → 번역 생략 (영어 원문 유지)")

        return content

    # 짧은 경우: 통째로 번역
    if len(content) <= GPT_MAX_CHARS:
        translated = _gpt_translate_chunk(content, api_key)

        return translated if translated else content

    # 긴 경우: 빈 줄(\n\n) 기준으로 청크 분할
    paragraphs = content.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 > GPT_MAX_CHARS and current:
            chunks.append(current.strip())
            current = para
        else:
            current = (current + "\n\n" + para).strip() if current else para

    if current:
        chunks.append(current.strip())

    # 청크별 번역 후 합치기
    translated_parts = []

    for idx, chunk in enumerate(chunks, 1):
        print(f"      번역 중... ({idx}/{len(chunks)} 청크)", end="\r")

        result = _gpt_translate_chunk(chunk, api_key)
        translated_parts.append(result if result else chunk)  # 실패 시 원문 폴백

    print()  # 줄바꿈 정리

    return "\n\n".join(translated_parts)

# [PubMed API 유틸]
def build_params(extra: dict) -> dict:
    """공통 파라미터 + 추가 파라미터 병합"""
    params = {
        "db":      "pubmed",
        "retmode": "xml",
        "tool":    "skin_chatbot_collector",
        "email":   DEFAULT_EMAIL,
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    params.update(extra)

    return params


def esearch(query: str, filter_str: str, max_results: int) -> list[str]:
    """ESearch: 검색어 → PMIDs 리스트 반환"""
    full_query = f"({query}) AND {filter_str}" if filter_str else query
    params = build_params({
        "term":       full_query,
        "retmax":     max_results,
        "sort":       "relevance",
        "usehistory": "n",
    })

    try:
        resp = requests.get(ESEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [ERROR] ESearch 실패: {e}")

        return []

    try:
        root  = ET.fromstring(resp.content)
        pmids = [el.text for el in root.findall(".//Id")]
        count = root.findtext("Count") or "0"

        print(f"    검색 결과: {count}건 중 {len(pmids)}개 PMIDs 수집")

        return pmids
    except ET.ParseError as e:
        print(f"    [ERROR] ESearch XML 파싱 실패: {e}")

        return []

def efetch_articles(pmids: list[str]) -> list[dict]:
    """EFetch: PMIDs → 논문 메타 + Abstract 파싱"""
    if not pmids:
        return []

    params = build_params({
        "id":      ",".join(pmids),
        "rettype": "abstract",
    })

    try:
        resp = requests.get(EFETCH_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"    [ERROR] EFetch 실패: {e}")

        return []

    return parse_pubmed_xml(resp.content)

def parse_pubmed_xml(xml_bytes: bytes) -> list[dict]:
    """PubmedArticleSet XML → 논문 딕셔너리 리스트"""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"    [ERROR] EFetch XML 파싱 실패: {e}")

        return []

    articles = []
    for article_el in root.findall(".//PubmedArticle"):
        try:
            art = parse_single_article(article_el)
            if art:
                articles.append(art)
        except Exception as e:
            print(f"    [WARN] 단건 파싱 오류 (건너뜀): {e}")

    return articles


def get_text(el: Optional[ET.Element], path: str, default: str = "") -> str:
    """XPath 경로에서 텍스트를 안전하게 추출 (하위 태그 텍스트 합산)"""
    if el is None:
        return default
    
    found = el.find(path)

    if found is None:
        return default
    
    return "".join(found.itertext()).strip()

def parse_abstract(article_el: ET.Element) -> str:
    """
    Abstract 텍스트 추출.
    구조화된 Abstract(Background/Methods/Results/Conclusions)도 섹션 레이블 유지.
    """
    abstract_el = article_el.find(".//Abstract")

    if abstract_el is None:
        return ""

    parts = []

    for text_el in abstract_el.findall("AbstractText"):
        label   = text_el.get("Label", "")
        content = "".join(text_el.itertext()).strip()
        parts.append(f"[{label}] {content}" if label else content)

    return "\n".join(parts).strip()

def parse_authors(article_el: ET.Element) -> str:
    """저자 목록 → '성 이름, ...' 문자열 (최대 5명 + et al.)"""
    authors = []

    for author_el in article_el.findall(".//Author"):
        last = get_text(author_el, "LastName")
        fore = get_text(author_el, "ForeName")
        name = f"{last} {fore}".strip() if (last or fore) else get_text(author_el, "CollectiveName")

        if name:
            authors.append(name)

    return ", ".join(authors[:5]) + (" et al." if len(authors) > 5 else "")


def parse_single_article(article_el: ET.Element) -> Optional[dict]:
    """PubmedArticle 단건 XML → 딕셔너리"""
    medline  = article_el.find("MedlineCitation")

    if medline is None:
        return None
    
    art_node = medline.find("Article")

    if art_node is None:
        return None

    pmid     = get_text(medline, "PMID")
    title    = get_text(art_node, "ArticleTitle")
    abstract = parse_abstract(art_node)
    authors  = parse_authors(art_node)
    journal  = get_text(art_node, "Journal/Title")
    volume   = get_text(art_node, "Journal/JournalIssue/Volume")
    issue    = get_text(art_node, "Journal/JournalIssue/Issue")
    pub_year = (
        get_text(art_node, "Journal/JournalIssue/PubDate/Year")
        or get_text(art_node, "Journal/JournalIssue/PubDate/MedlineDate")[:4]
    )
    pages    = get_text(art_node, "Pagination/MedlinePgn")

    mesh_terms = [
        get_text(mesh_el, "DescriptorName")
        for mesh_el in article_el.findall(".//MeshHeading")
    ]
    keywords = [
        "".join(kw.itertext()).strip()
        for kw in article_el.findall(".//Keyword")
    ]

    if not title and not abstract:
        return None

    return {
        "pmid":     pmid,
        "title":    title,
        "abstract": abstract,
        "authors":  authors,
        "journal":  journal,
        "volume":   volume,
        "issue":    issue,
        "year":     pub_year,
        "pages":    pages,
        "mesh":     mesh_terms,
        "keywords": keywords,
    }

# [content 빌더]
def build_content(art: dict, label: str) -> str:
    """
    논문 메타 + Abstract → content 텍스트 생성.
    """
    lines = [
        f"[주제] {label}",
        f"Title: {art['title']}",
    ]

    if art["abstract"]:
        lines.append("")
        lines.append("[Abstract]")
        lines.append(art["abstract"])

    if art["keywords"]:
        lines.append("")
        lines.append(f"Keywords: {', '.join(art['keywords'][:10])}")

    if art["mesh"]:
        lines.append(f"MeSH: {', '.join(art['mesh'][:10])}")

    return "\n".join(lines)

# [논문 → 벡터DB 포맷 변환]
def transform_article(art: dict, query_meta: dict, openai_key: str, chunk_index: int=0) -> dict:
    """
    논문 딕셔너리 → vectordb_insert.py 호환 JSON 포맷.

    - 태깅: 번역 전 영어 원문 기준 수행 (키워드 매칭 정확도 유지)
    - 번역: TRANSLATE_ENABLED=True 이고 openai_key 가 있을 때만 실행
    """
    # content 생성
    content = build_content(art, query_meta["label"])

    # 태깅 (영어 원문 기준 → 정확도 유지)
    classify_text = (
        f"{art['title']} {art['abstract']} "
        f"{' '.join(art['keywords'])} {' '.join(art['mesh'])}"
    )

    tags = resolve_tags(classify_text)

    # GPT 번역
    if TRANSLATE_ENABLED and openai_key:
        content = translate_content(content, openai_key)
    elif TRANSLATE_ENABLED and not openai_key:
        print("      [WARN] OPENAI_API_KEY 미설정 → 영어 원문 저장")

    return {
        "id":             f"pubmed_{art['pmid']}_{chunk_index:02d}",
        "doc_type":       query_meta["doc_type"],
        "category":       query_meta.get("category", ""),
        "skin_type":      tags["skin_type"],
        "concern_tag":    tags["concern_tag"],
        "ingredient_tag": tags["ingredient_tag"],
        "source":         "pubmed",
        "chunk_index":    chunk_index,
        "content":        content
    }

# [메인 수집 로직]
def collect(max_per_query: int, required_extra: int, openai_key: str, queries: list[dict] | None = None) -> list[dict]:
    """
    쿼리 목록 순회 → ESearch → EFetch → 변환(번역 포함)

    Args:
        max_per_query:  일반 쿼리당 수집 논문 수
        required_extra: required=True 쿼리의 추가 수집량
        openai_key:     GPT 번역용 OpenAI API 키
        queries:        사용할 쿼리 목록 (None이면 내부 SEARCH_QUERIES fallback)
    """
    all_docs: list[dict]  = []
    seen_pmids: set[str]  = set()
    query_list = queries if queries is not None else SEARCH_QUERIES
    total = len(query_list)

    for i, q_meta in enumerate(query_list, 1):
        label  = q_meta["label"]
        is_req = q_meta.get("required", False)
        max_n  = max_per_query + required_extra if is_req else max_per_query

        print(f"\n[{i:02d}/{total}] {label} {'[필수]' if is_req else ''}")
        print(f"  쿼리: {q_meta['query']}")

        # ESearch
        time.sleep(REQUEST_DELAY)
        pmids = esearch(q_meta["query"], q_meta.get("filter", ""), max_n)

        if not pmids:
            print("  → PMIDs 없음, 건너뜀")

            continue

        # 중복 PMID 제거
        new_pmids = [p for p in pmids if p not in seen_pmids]

        if len(pmids) != len(new_pmids):
            print(f"  → 중복 PMID {len(pmids) - len(new_pmids)}개 제외 → {len(new_pmids)}개 신규")

        seen_pmids.update(new_pmids)

        if not new_pmids:
            print("  → 신규 PMID 없음, 건너뜀")

            continue

        # EFetch
        time.sleep(REQUEST_DELAY)
        articles = efetch_articles(new_pmids)

        print(f"  → 논문 파싱 완료: {len(articles)}건")

        # 변환 + 번역
        for j, art in enumerate(articles):
            print(f"    [{j + 1}/{len(articles)}] PMID {art['pmid']} 처리 중...")

            doc = transform_article(art, q_meta, openai_key=openai_key, chunk_index=j)
            all_docs.append(doc)

    return all_docs

def save_json(docs: list[dict], output_dir: Path, filename: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    size_kb = path.stat().st_size / 1024

    print(f"\n[저장 완료]")
    print(f"  경로: {path}")
    print(f"  건수: {len(docs):,}건")
    print(f"  크기: {size_kb:.1f} KB\n")

    return path

def print_summary(docs: list[dict]) -> None:
    """카테고리별 수집 통계 출력"""
    from collections import Counter

    cat_counts = Counter(d["category"] for d in docs)
    doc_counts = Counter(d["doc_type"] for d in docs)

    print("=" * 55)
    print(f"  수집 완료: {len(docs):,}건")
    print("-" * 55)
    print("  doc_type 분포:")

    for dt, cnt in sorted(doc_counts.items()):
        print(f"    {dt:15s}: {cnt:4d}건")

    print("  category 분포:")

    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {cat:35s}: {cnt:4d}건")

    print("=" * 55)

# [진입점]
def main():
    global DEFAULT_EMAIL, NCBI_API_KEY, REQUEST_DELAY, TRANSLATE_ENABLED

    parser = argparse.ArgumentParser(
        description="PubMed E-utilities 기반 피부 가이드/성분 데이터 수집 + GPT 번역",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--max-per-query", type=int, default=DEFAULT_MAX_PER_QUERY,
        help=f"쿼리당 최대 수집 논문 수 (기본값: {DEFAULT_MAX_PER_QUERY})",
    )
    parser.add_argument(
        "--required-extra", type=int, default=5,
        help="required=True 쿼리의 추가 수집량 (기본값: 5)",
    )
    parser.add_argument(
        "--output-dir", type=str, default=str(OUTPUT_DIR),
        help=f"JSON 저장 경로 (기본값: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--output-file", type=str, default=OUTPUT_FILE,
        help=f"출력 파일명 (기본값: {OUTPUT_FILE})",
    )
    parser.add_argument(
        "--email", type=str, default=DEFAULT_EMAIL,
        help="NCBI 정책상 필요한 연락 이메일",
    )
    parser.add_argument(
        "--ncbi-key", type=str, default=NCBI_API_KEY,
        help="NCBI API 키 (없어도 동작, 속도 제한 완화)",
    )
    parser.add_argument(
        "--openai-key", type=str, default=OPENAI_API_KEY,
        help="OpenAI API 키 (GPT 번역용, .env의 OPENAI_API_KEY 대체 가능)",
    )
    parser.add_argument(
        "--queries-file", type=str, default=None,
        help=(
            "쿼리 문자열 배열 JSON 파일 경로\n"
            "예: ./assets/links/pubmed_queries.json\n"
            "미지정 시 스크립트 내부 SEARCH_QUERIES 사용 (fallback)"
        ),
    )
    parser.add_argument(
        "--no-translate", action="store_true",
        help="GPT 번역 생략 → 영어 원문 그대로 저장",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="실제 API 호출 없이 쿼리 목록만 출력",
    )

    args = parser.parse_args()

    # 전역 설정 반영
    if args.email:
        DEFAULT_EMAIL = args.email
    if args.ncbi_key:
        NCBI_API_KEY  = args.ncbi_key
        REQUEST_DELAY = 0.11
    if args.no_translate:
        TRANSLATE_ENABLED = False

    # OpenAI 키: CLI 인자 > .env 순
    openai_key = args.openai_key or OPENAI_API_KEY

    # 외부 쿼리 파일 로드 (지정 시) / fallback: 내부 SEARCH_QUERIES
    queries = None

    if args.queries_file:
        queries_path = Path(args.queries_file)
        try:
            queries = load_queries_from_file(queries_path, openai_key)
        except (FileNotFoundError, ValueError) as e:
            print(f"\n[ERROR] 쿼리 파일 로드 실패: {e}")

            return
    else:
        print("\n  [INFO] --queries-file 미지정 → 내부 SEARCH_QUERIES 사용 (fallback)")

        queries = None  # collect()에서 SEARCH_QUERIES 사용

    # 실행 정보 출력
    translate_status = (
        "사용 안 함 (--no-translate)"
        if not TRANSLATE_ENABLED
        else (f"활성화 ({GPT_MODEL})" if openai_key else "비활성화 (OPENAI_API_KEY 없음 → 영어 원문 저장)")
    )
    print("\n" + "=" * 60)
    print("  PubMed E-utilities 피부 데이터 수집기")
    print("=" * 60)
    print(f"  이메일      : {DEFAULT_EMAIL}")
    print(f"  NCBI 키     : {'설정됨 (10 req/s)' if NCBI_API_KEY else '없음 (3 req/s)'}")
    print(f"  GPT 번역    : {translate_status}")

    query_count = len(queries) if queries is not None else len(SEARCH_QUERIES)
    queries_src = f"외부 파일 ({args.queries_file})" if args.queries_file else "내부 SEARCH_QUERIES"

    print(f"  쿼리 소스   : {queries_src}")
    print(f"  쿼리 수     : {query_count}개")
    print(f"  쿼리당 수집 : {args.max_per_query}건")
    print(f"  tagging     : utils/tagging.py")
    print("=" * 60)

    if args.dry_run:
        dry_list = queries if queries is not None else SEARCH_QUERIES

        print("\n[DRY RUN] 쿼리 목록:")

        for i, q in enumerate(dry_list, 1):
            req = "[필수]" if q.get("required") else ""

            print(f"  {i:02d}. [{q['doc_type']}] {q['label']} {req}")
            print(f"       → {q['query']}")

        return

    # 수집 실행
    docs = collect(
        max_per_query=args.max_per_query,
        required_extra=args.required_extra,
        openai_key=openai_key,
        queries=queries,
    )

    if not docs:
        print("\n[ERROR] 수집된 데이터가 없습니다. 네트워크 및 API 설정을 확인하세요.")

        return

    print_summary(docs)
    save_json(docs, Path(args.output_dir), args.output_file)

if __name__ == "__main__":
    main()