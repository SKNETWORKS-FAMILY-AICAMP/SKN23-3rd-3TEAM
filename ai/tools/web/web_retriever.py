from typing import List, Dict
from ai.tools.web.web_search import web_search
from ai.tools.web.web_fetch import fetch_url_text
from ai.tools.web.web_extract import extract_relevant_snippets

def _to_passage(item: Dict, snippet: str, dist: float) -> Dict:
    url = item.get("url", "")
    title = item.get("title", "")
    dist = float(max(0.0, min(dist, 1.0)))  # 0~1로 클립
    return {
        "source_id": f"web:{url}" if url else "web:unknown",
        "snippet": snippet,
        "distance": dist,
        "score": 1.0 - dist,
        "meta": {
            "source_type": "web",
            "url": url,
            "title": title,
        },
    }

def search_web(query: str, top_k: int = 3, bias: str | None = None) -> List[Dict]:
    if bias:
        query = f"{query} {bias}"
    results = web_search(query, k=max(top_k * 3, 8))
    passages: List[Dict] = []

    for idx, item in enumerate(results):
        url = item.get("url", "")
        base_snip = (item.get("snippet") or "").strip()

        snippets = []
        if url:
            try:
                text = fetch_url_text(url)
                snippets = extract_relevant_snippets(text, query, max_snippets=2)
            except Exception:
                snippets = []

        if not snippets and base_snip:
            snippets = [base_snip[:500]]

        # dist는 간단히 “검색랭크 기반”으로 부여 (idx 작을수록 더 좋게)
        # idx=0 -> dist=0.15, idx=1 -> 0.25 ... 이런 식
        dist = min(0.15 + 0.10 * idx, 0.8)

        for sn in snippets:
            passages.append(_to_passage(item, sn, dist))

        if len(passages) >= top_k:
            break

    return passages[:top_k]