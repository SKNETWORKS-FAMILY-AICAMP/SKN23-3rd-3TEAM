"""
대한피부과학회 피부질환 페이지 → 벡터DB JSON 변환 스크립트
=============================================================

링크 입력 파일 포맷:
  [형식 A] {"질환명": "URL", ...}                    ← 기본 형식
  [형식 B] ["https://...", ...]                      ← URL 문자열 배열
  [형식 C] [{"url": "https://...", ...}, ...]        ← 객체 배열
  [형식 D] .txt, 한 줄에 URL 하나 (# 주석 지원)

출력:
  - vectordb_insert.py 호환 JSON (벡터DB 메타 포맷)

사용법:
  python derma_to_vectordb.py --input links.json
  python derma_to_vectordb.py --input links.json --output result.json
  python derma_to_vectordb.py --input links.txt --delay 1.0
"""

import re
import sys
import json
import time
import argparse
import requests

from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.tagging import match_all_tags

# ─────────────────────────────────────────────────────────────
# [설정]
# ─────────────────────────────────────────────────────────────

URL_FILE        = "assets/derma_skin_disease.json"
OUTPUT_DIR      = Path("./assets/vector_data")
OUTPUT_FILE     = "derma_disease.jsonl"
REQUEST_DELAY   = 0.5    # 요청 간 딜레이(초) — 서버 부하 방지
REQUEST_TIMEOUT = 15     # 타임아웃(초)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 인식할 섹션 키워드
SECTION_KEYWORDS = [
    "정의", "증상", "원인", "원인 및 증상", "치료", "예후",
    "병리조직소견", "진단", "합병증", "경과", "주의사항",
]


# 링크 파일 로더
def load_links(file_path: str) -> list[dict]:
    """
    txt 또는 json 파일에서 URL 목록을 읽어 반환.

    반환 형식: [{"title": "질환명", "url": "https://..."}, ...]

    지원 포맷:
      [형식 A] {"질환명": "URL", ...}                ← 기본 형식
      [형식 B] ["https://...", ...]                  ← URL 문자열 배열
      [형식 C] [{"url": "https://...", ...}, ...]    ← 객체 배열
      [형식 D] .txt, 한 줄에 URL 하나 (# 주석 지원)
    """
    path   = Path(file_path)
    suffix = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"링크 파일을 찾을 수 없습니다: {path}")

    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))

        # [형식 A] {"질환명": "URL", ...}
        if isinstance(data, dict):
            return [
                {"title": title, "url": url.strip()}
                for title, url in data.items()
                if url.strip()
            ]

        # [형식 B, C] 배열
        if isinstance(data, list):
            result = []

            for item in data:
                if isinstance(item, str):
                    result.append({"title": "", "url": item.strip()})
                elif isinstance(item, dict):
                    url   = item.get("url") or item.get("link") or item.get("href", "")
                    title = item.get("title") or item.get("name", "")

                    if url:
                        result.append({"title": title, "url": url.strip()})

            return result

        raise ValueError("JSON 파일 형식을 인식할 수 없습니다.")

    raise ValueError(f"지원하지 않는 파일 형식: {suffix}  (지원: .json)")

# 크롤링
def fetch_html(url: str) -> str | None:
    """URL → HTML 반환, 실패 시 None"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding    # 한글 인코딩 자동 감지

        return resp.text
    except requests.exceptions.RequestException as e:
        print(f"    [ERROR] 요청 실패: {e}")

        return None

# 파싱
def parse_uid(url: str) -> str:
    """URL에서 uid 파라미터 추출"""
    m = re.search(r"uid=(\d+)", url)

    return m.group(1) if m else "unknown"

def parse_disease_page(html: str, url: str) -> dict | None:
    """
    대한피부과학회 피부질환 상세 페이지 파싱.

    반환값:
        {
            "title":      질환명,
            "created_at": 작성일 (YYYY.MM.DD),
            "sections":   {"정의": "...", "증상": "...", ...},
            "content":    벡터화용 전체 텍스트,
            "url":        원본 URL,
        }
        파싱 실패 시 None
    """
    soup = BeautifulSoup(html, "html.parser")

    # ── 질환명 + 작성일 ──────────────────────────────────────
    title      = ""
    created_at = ""

    title_cell = soup.find("td", attrs={"colspan": True})
    if title_cell:
        raw        = title_cell.get_text(separator="\n").strip()
        first_line = raw.split("\n")[0].strip()
        # "혈관육종  2016.02.16 작성자 : 관리자 조회 : 12015"
        title = re.split(r"\s{2,}|\t", first_line)[0].strip()
        m = re.search(r"(\d{4}\.\d{2}\.\d{2})", raw)
        
        if m:
            created_at = m.group(1)

    # 대안: 첫 번째 <strong> 텍스트
    if not title:
        for tag in soup.find_all("strong"):
            t = tag.get_text(strip=True)

            if t and len(t) < 50:
                title = t
                break

    # ── 본문 <td> 탐색 ───────────────────────────────────────
    content_td = None
    
    for td in soup.find_all("td"):
        text = td.get_text(separator="\n").strip()

        if len(text) > 200 and any(kw in text for kw in ["정의", "증상", "치료"]):
            content_td = td
            break

    if content_td is None:
        print(f"    [WARN] 본문 영역 미발견: {url}")

        return None

    raw_content = content_td.get_text(separator="\n").strip()

    # ── 섹션 분리 ────────────────────────────────────────────
    sections      = {}
    current_sec   = "본문"
    current_lines = []

    for line in raw_content.splitlines():
        s = line.strip()
        if not s:
            continue

        matched_kw = None
        for kw in SECTION_KEYWORDS:
            if re.fullmatch(rf"[\*\[\]<>]*{kw}[\*\[\]<>]*", s):
                matched_kw = kw
                break

        if matched_kw:
            if current_lines:
                sections[current_sec] = "\n".join(current_lines).strip()
            current_sec   = matched_kw
            current_lines = []
        else:
            current_lines.append(s)

    if current_lines:
        sections[current_sec] = "\n".join(current_lines).strip()

    # ── content 텍스트 구성 ──────────────────────────────────
    parts = [f"질환명: {title}"]
    for sec_name, sec_text in sections.items():
        if sec_name == "본문" and not sec_text:
            continue
        parts.append(f"\n[{sec_name}]\n{sec_text}")

    content = "\n".join(parts).strip()

    return {
        "title":      title,
        "created_at": created_at,
        "sections":   sections,
        "content":    content,
        "url":        url,
    }

# 벡터DB 메타 포맷 변환
def transform_to_vector_doc(parsed: dict, seq_no: int, title_override: str = "") -> dict:
    """
    파싱 결과 → 벡터DB 메타 포맷 변환.

    Args:
        parsed:         parse_disease_page() 반환값
        seq_no:         순번 (ID 생성용)
        title_override: 링크 파일의 질환명 키 (파싱 제목 없을 때 폴백)
    """
    content = parsed["content"]
    uid     = parse_uid(parsed["url"])

    # 파싱 제목 우선, 없으면 링크 파일 키값 사용
    if title_override and not parsed["title"]:
        content = re.sub(r"^질환명:.*", f"질환명: {title_override}", content)

    tags = match_all_tags(content)    # utils.tagging 에서 전체 태그 한 번에 처리

    return {
        "id":             f"derma_disease_{uid}_{seq_no:04d}",
        "doc_type":       "guide",
        "category":       tags["category"][0] if tags["category"] else "general",
        "skin_type":      tags["skin_type"],
        "concern_tag":    tags["concern_tag"],
        "ingredient_tag": tags["ingredient_tag"],
        "source":         "derma_kr",
        "chunk_index":    0,
        "content":        content,
    }

# URL 목록 → 문서 제너레이터
def iter_docs(items: list[dict], delay: float):
    """URL 목록을 순회하며 변환된 문서를 yield하는 제너레이터"""
    total = len(items)
    success, fail = 0, 0

    for i, item in enumerate(items, start=1):
        url           = item["url"]
        title_in_file = item["title"]

        print(f"  [{i:>3}/{total}] {url}")

        html = fetch_html(url)

        if html is None:
            fail += 1
            continue

        parsed = parse_disease_page(html, url)

        if parsed is None:
            fail += 1
            continue

        doc = transform_to_vector_doc(parsed, seq_no=i, title_override=title_in_file)
        display_title = parsed["title"] or title_in_file or "(제목 없음)"

        print(f"         ✓ {display_title}"
              f"  |  category: {doc['category']}"
              f"  |  concern_tag: {doc['concern_tag']}")

        success += 1
        yield doc

        if i < total:
            time.sleep(delay)

    print(f"\n  크롤링 완료: 성공 {success}건 / 실패 {fail}건")


# JSONL 저장 (제너레이터 입력)
def save_jsonl(docs_iter, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0

    with open(output_path, "w", encoding="utf-8") as f:
        for doc in docs_iter:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            count += 1

    return count


# 메인 실행
def run(input_file: str, output_path: Path, delay: float) -> None:
    # 1. 링크 파일 로드
    print(f"\n[1] 링크 파일 로드: {input_file}")

    items = load_links(input_file)

    print(f"    총 {len(items)}개 URL 발견")

    if not items:
        print("    [ERROR] URL이 없습니다. 파일 내용을 확인해주세요.")
        return

    # 2. 크롤링 및 파싱 → 스트리밍 저장
    print(f"\n[2] 크롤링 시작 (딜레이: {delay}초)\n")

    count = save_jsonl(iter_docs(items, delay), output_path)

    # 3. 완료 출력
    print(f"\n[3] JSONL 저장: {output_path}")
    print(f"\n{'=' * 55}")
    print(f"  완료: {count}건 저장")
    print(f"  출력 파일: {output_path}"
          f"  ({output_path.stat().st_size / 1024:.1f} KB)")
    print(f"{'=' * 55}\n")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="대한피부과학회 피부질환 링크 → 벡터DB JSON 변환"
    )
    parser.add_argument(
        "--output", "-o",
        default=str(OUTPUT_DIR / OUTPUT_FILE),
        help=f"출력 JSONL 경로 (기본: {OUTPUT_DIR / OUTPUT_FILE})"
    )
    parser.add_argument(
        "--delay", "-d", type=float, default=REQUEST_DELAY,
        help=f"요청 딜레이(초) (기본: {REQUEST_DELAY})"
    )
    args = parser.parse_args()

    run(input_file=URL_FILE, output_path=Path(args.output), delay=args.delay)

if __name__ == "__main__":
    main()