"""
AAD(American Academy of Dermatology) 페이지 → 벡터DB JSON 변환 스크립트
==========================================================================

AAD 사이트의 두 가지 페이지 타입을 모두 처리합니다:
  - [guide]   /public/everyday-care/...  일상 피부 관리 가이드
  - [disease] /public/diseases/...       피부 질환 정보

링크 입력 파일 포맷:
  - json: ["https://www.aad.org/...", ...]
  - txt : 한 줄에 URL 하나 (# 주석 지원)

출력:
  - vectordb_insert.py 호환 JSON (벡터DB 메타 포맷)
  - source: "aad_org"

사용법:
  python aad_to_vectordb.py
  python aad_to_vectordb.py --output result.json
  python aad_to_vectordb.py --delay 1.5
"""

import os
import re
import sys
import json
import time
import argparse
import requests

from pathlib import Path
from dotenv import load_dotenv
from bs4 import BeautifulSoup, Tag, NavigableString
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.tagging import match_all_tags

load_dotenv()

# ─────────────────────────────────────────────────────────────
# [설정]
# ─────────────────────────────────────────────────────────────
URL_FILE        = "./assets/aad_skin_care_disease2.json"
OUTPUT_DIR      = Path("./assets/vector_data")
OUTPUT_FILE     = "aad_guides2.json"
REQUEST_DELAY   = 1.0
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# 본문에서 제거할 노이즈 문구 (소문자 포함 여부로 판단)
NOISE_PATTERNS = [
    "american academy of dermatology",
    "reproduction or republication",
    "advertising helps support",
    "privacy policy",
    "terms of use",
]
# ── GPT 번역 설정 ─────────────────────────────────────────────
GPT_MODEL        = "gpt-4o-mini"   # 번역 품질 대비 비용 최적 모델
GPT_MAX_CHARS    = 2000            # 섹션 1개당 최대 글자 수 (초과 시 분할)
GPT_RETRY        = 2               # 번역 실패 시 재시도 횟수
GPT_RETRY_DELAY  = 3.0             # 재시도 대기(초)

TRANSLATE_SYSTEM_PROMPT = """You are a professional Korean medical translator specializing in dermatology.
Translate the given English skin care / dermatology text into natural Korean.

Rules:
- Translate only the actual content text
- Keep structural markers exactly as-is: "Title:", "[섹션명]", "• ", "Last updated:"
- Keep ingredient names, brand names, and medical terms accurate
- Use formal Korean (합쇼체 아닌 해요체)
- Output only the translated text, no explanations"""

# 섹션 구분 heading 태그
SECTION_HEADINGS = {"h2", "h3", "h4"}

# URL 분류
def classify_url(url: str) -> dict:
    """URL 경로로 페이지 타입(guide/disease) 분류"""
    path  = url.replace("https://www.aad.org", "").strip("/")
    parts = [p for p in path.split("/") if p]
    slug  = parts[-1] if parts else "unknown"

    if len(parts) >= 2 and parts[0] == "public" and parts[1] == "diseases":
        disease = parts[2] if len(parts) > 2 else ""
        return {"page_type": "disease", "slug": slug, "disease": disease}

    return {"page_type": "guide", "slug": slug, "disease": ""}

# 링크 파일 로더
def load_links(file_path: str) -> list[str]:
    """JSON 또는 TXT 파일에서 URL 목록 로드"""
    path   = Path(file_path)
    suffix = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"링크 파일을 찾을 수 없습니다: {path}")

    if suffix == ".txt":
        lines = path.read_text(encoding="utf-8").splitlines()
        return [ln.strip() for ln in lines
                if ln.strip() and not ln.strip().startswith("#")]

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            urls = []
            for item in data:
                if isinstance(item, str):
                    urls.append(item.strip())
                elif isinstance(item, dict):
                    url = item.get("url") or item.get("link") or ""
                    if url:
                        urls.append(url.strip())
            return urls
        raise ValueError("JSON 파일은 URL 배열 형식이어야 합니다.")

    raise ValueError(f"지원하지 않는 파일 형식: {suffix}")

# 크롤링
def fetch_html(url: str) -> str | None:
    """URL → HTML 반환, 실패 시 None"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as e:
        print(f"    [ERROR] 요청 실패: {e}")
        return None

# 파싱 핵심 로직
def is_noise(text: str) -> bool:
    """푸터/광고성 문구인지 확인"""
    tl = text.lower()
    return any(p in tl for p in NOISE_PATTERNS)


def extract_title(soup: BeautifulSoup) -> tuple[str, Tag | None]:
    """
    페이지 제목과 h1 태그 자체를 반환.
    h1 태그 위치를 알아야 이후 형제 탐색이 가능.
    """
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True), h1

    title_tag = soup.find("title")
    if title_tag:
        return title_tag.get_text(strip=True).split("|")[0].strip(), None

    return "", None


def extract_last_updated(soup: BeautifulSoup) -> str:
    """'Last updated: ...' 날짜 추출"""
    pattern = re.compile(r"last\s+updated[:\s]+(.+?)(?:\s*$)", re.I)
    for tag in soup.find_all(["p", "em", "span", "i"]):
        m = pattern.search(tag.get_text(strip=True))
        if m:
            return m.group(1).strip().strip("*").strip()
    return ""


def iter_body_after_h1(h1_tag: Tag):
    """
    h1 태그 이후에 나오는 모든 요소를 순서대로 yield.

    전략:
      - h1이 body 직속 자식이면 → h1 이후 형제를 재귀 탐색
      - h1이 어떤 div 안에 있으면 → 그 div의 이후 형제도 포함

    AAD 구조상 h1이 body 직속이거나 content div 안에 있으므로
    h1 이후의 document order로 모든 태그를 순회.
    """
    # h1 이후 문서 순서로 모든 태그 순회
    # find_all_next()는 h1 이후 DOM 순서 전체를 반환
    for tag in h1_tag.find_all_next(True):
        yield tag

def collect_blocks_after_h1(h1_tag: Tag) -> list[dict]:
    """
    h1 이후의 요소들에서 본문 블록(heading/text/list)을 수집.

    - h1.find_all_next()로 문서 순서 보장
    - 노이즈 문구 필터링
    - 중복 방지 (li는 부모 ul/ol 처리 시 함께 처리)
    """
    blocks: list[dict] = []
    seen:   set[int]   = set()

    for tag in iter_body_after_h1(h1_tag):
        tid = id(tag)
        if tid in seen:
            continue

        name = tag.name
        if not name:
            continue

        # ── heading ──────────────────────────────────────────
        if name in SECTION_HEADINGS:
            text = tag.get_text(strip=True)
            if text and len(text) < 200 and not is_noise(text):
                blocks.append({"type": "heading", "text": text})
            continue

        # ── 문단 ─────────────────────────────────────────────
        if name == "p":
            text = tag.get_text(separator=" ", strip=True)
            if text and len(text) > 15 and not is_noise(text):
                blocks.append({"type": "text", "text": text})
            continue

        # ── 리스트 아이템 ─────────────────────────────────────
        if name == "li" and isinstance(tag.parent, Tag) and tag.parent.name in {"ul", "ol"}:
            seen.add(tid)
            text = tag.get_text(separator=" ", strip=True)
            if text and len(text) > 5 and not is_noise(text):
                blocks.append({"type": "list", "text": "• " + text})
            continue

    return blocks

def assemble_content(title: str, blocks: list[dict], last_updated: str) -> tuple[str, dict]:
    """블록 리스트 → (content 전체 텍스트, sections dict)"""
    sections:      dict[str, str] = {}
    current_sec:   str | None     = None
    current_lines: list[str]      = []
    intro_lines:   list[str]      = []

    for block in blocks:
        if block["type"] == "heading":
            if current_sec is not None:
                if current_lines:
                    sections[current_sec] = "\n".join(current_lines).strip()
            else:
                intro_lines = current_lines[:]
            current_sec   = block["text"]
            current_lines = []
        else:
            current_lines.append(block["text"])

    if current_sec is not None:
        if current_lines:
            sections[current_sec] = "\n".join(current_lines).strip()
    else:
        intro_lines = current_lines[:]

    parts = [f"Title: {title}"]
    if intro_lines:
        parts.append("\n" + "\n".join(intro_lines))
    for sec_name, sec_text in sections.items():
        if sec_text:
            parts.append(f"\n[{sec_name}]\n{sec_text}")
    if last_updated:
        parts.append(f"\nLast updated: {last_updated}")

    return "\n".join(parts).strip(), sections

# 메인 파서
def parse_aad_page(html: str, url: str, url_meta: dict) -> dict | None:
    """
    AAD 페이지 파싱.

    처리 순서:
      1. HTML 파싱
      2. script/style 제거 (nav는 남김 — h1 이후 탐색으로 자연 배제)
      3. h1 태그 위치 파악
      4. h1 이후 형제 요소만 순서대로 수집 → 블록 생성
      5. content / sections 조립
    """
    soup = BeautifulSoup(html, "html.parser")

    # script/style만 제거 (nav 제거하면 h1 위치 탐색에 영향)
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()

    # 제목 + h1 태그 위치 확보
    title, h1_tag = extract_title(soup)
    last_updated  = extract_last_updated(soup)

    if not title:
        print(f"    [WARN] 제목 추출 실패: {url}")
        return None

    if h1_tag is None:
        print(f"    [WARN] h1 태그 없음, title 태그로만 제목 추출됨: {url}")
        # h1이 없으면 body 전체에서 블록 수집 시도 (fallback)
        body = soup.find("body") or soup
        blocks = []
        seen = set()
        for tag in body.find_all(["h2", "h3", "h4", "p", "li"]):
            tid = id(tag)
            if tid in seen:
                continue
            name = tag.name
            text = tag.get_text(separator=" ", strip=True)
            if not text or is_noise(text):
                continue
            if name in SECTION_HEADINGS and len(text) < 200:
                blocks.append({"type": "heading", "text": text})
            elif name == "p" and len(text) > 15:
                blocks.append({"type": "text", "text": text})
            elif name == "li" and len(text) > 5:
                seen.add(tid)
                blocks.append({"type": "list", "text": "• " + text})
    else:
        # h1 이후 형제 요소만 수집 (핵심 전략)
        blocks = collect_blocks_after_h1(h1_tag)

    if not blocks:
        print(f"    [WARN] 본문 블록 없음: {url}")
        return None

    content, sections = assemble_content(title, blocks, last_updated)

    if len(content) < 150:
        print(f"    [WARN] 본문 너무 짧음 ({len(content)}자): {url}")
        return None

    return {
        "title":        title,
        "last_updated": last_updated,
        "sections":     sections,
        "content":      content,
        "url":          url,
        "page_type":    url_meta["page_type"],
    }

# ─────────────────────────────────────────────────────────────
# GPT 번역
# ─────────────────────────────────────────────────────────────

def _gpt_translate_chunk(text: str, api_key: str) -> str | None:
    """
    텍스트 청크 1개를 GPT로 번역. 실패 시 None 반환.
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
        "temperature": 0.3,   # 번역은 낮은 temperature가 일관성↑
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
    content 전체를 GPT로 번역.

    전략:
      - "Title: ...", "[섹션명]" 구조는 그대로 유지되도록 프롬프트로 지시
      - GPT_MAX_CHARS 초과 시 빈 줄 기준으로 청크 분할 후 순서대로 번역
      - 청크 단위 실패 시 해당 청크만 영어 원문으로 폴백
    """
    # 짧으면 통째로 번역
    if len(content) <= GPT_MAX_CHARS:
        translated = _gpt_translate_chunk(content, api_key)

        return translated if translated else content

    # 긴 경우: 빈 줄 기준으로 분할
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
        translated_parts.append(result if result else chunk)   # 실패 시 원문 폴백

    print()  # 줄바꿈

    return "\n\n".join(translated_parts)

# 벡터DB 메타 포맷 변환
def make_doc_id(url: str, seq_no: int) -> str:
    """URL 경로 기반 고유 ID"""
    path = url.replace("https://www.aad.org", "").strip("/")
    safe = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")[:80]

    return f"aad_{safe}_{seq_no:04d}"

def transform_to_vector_doc(parsed: dict, seq_no: int) -> dict:
    """파싱 결과 → 벡터DB 메타 포맷"""
    content = parsed["content"]
    api_key = os.getenv("OPENAI_API_KEY")

    content = translate_content(content, api_key)
    tags    = match_all_tags(content)

    return {
        "id":             make_doc_id(parsed["url"], seq_no),
        "doc_type":       "guide",
        "category":       tags["category"][0] if tags["category"] else "general",
        "skin_type":      tags["skin_type"],
        "concern_tag":    tags["concern_tag"],
        "ingredient_tag": tags["ingredient_tag"],
        "source":         "aad_org",
        "chunk_index":    0,
        "content":        content,
    }

# 메인 실행
def run(input_file: str, output_path: Path, delay: float) -> None:
    print(f"\n[1] 링크 파일 로드: {input_file}")

    urls = load_links(input_file)

    print(f"    총 {len(urls)}개 URL 발견")

    if not urls:
        print("    [ERROR] URL이 없습니다.")

        return

    guide_cnt   = sum(1 for u in urls if classify_url(u)["page_type"] == "guide")
    disease_cnt = len(urls) - guide_cnt

    print(f"    guide: {guide_cnt}개 / disease: {disease_cnt}개\n")

    print(f"[2] 크롤링 시작 (딜레이: {delay}초)\n")

    results, success, fail = [], 0, 0

    for i, url in enumerate(urls, start=1):
        url_meta = classify_url(url)
        label    = f"[{url_meta['page_type']:7}]"

        print(f"  [{i:>3}/{len(urls)}] {label} {url}")

        html = fetch_html(url)

        if html is None:
            fail += 1
            continue

        parsed = parse_aad_page(html, url, url_meta)

        if parsed is None:
            fail += 1
            continue

        doc = transform_to_vector_doc(parsed, seq_no=i)
        results.append(doc)

        print(f"           ✓ {parsed['title']}")
        print(f"             category: {doc['category']}"
              f"  |  concern_tag: {doc['concern_tag']}"
              f"  |  본문 {len(parsed['content'])}자")
        
        success += 1

        if i < len(urls):
            time.sleep(delay)

    print(f"\n[3] JSON 저장: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 55}")
    print(f"  완료: 성공 {success}건 / 실패 {fail}건")
    print(f"  출력 파일: {output_path}"
          f"  ({output_path.stat().st_size / 1024:.1f} KB)")
    print(f"{'=' * 55}\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="AAD 피부 가이드/질환 페이지 → 벡터DB JSON 변환"
    )
    parser.add_argument("--output", "-o",
                        default=str(OUTPUT_DIR / OUTPUT_FILE),
                        help=f"출력 JSON 경로 (기본: {OUTPUT_DIR / OUTPUT_FILE})")
    parser.add_argument("--delay",  "-d", type=float, default=REQUEST_DELAY,
                        help=f"요청 딜레이(초) (기본: {REQUEST_DELAY})")
    args = parser.parse_args()

    run(input_file=URL_FILE, output_path=Path(args.output), delay=args.delay)

if __name__ == "__main__":
    main()