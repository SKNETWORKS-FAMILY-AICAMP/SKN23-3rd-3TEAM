import re
from typing import List

def extract_relevant_snippets(text: str, query: str, max_snippets: int = 3) -> List[str]:
    # 아주 단순 버전: 문장 단위로 쪼개서 query 키워드 포함 우선
    keywords = [kw for kw in re.split(r"\s+", query) if len(kw) >= 2]
    sents = re.split(r"(?<=[.!?。])\s+|\n+", text)

    scored = []
    for s in sents:
        score = sum(1 for kw in keywords if kw.lower() in s.lower())
        if score > 0 and 40 <= len(s) <= 400:
            scored.append((score, s.strip()))
    scored.sort(key=lambda x: x[0], reverse=True)

    return [s for _, s in scored[:max_snippets]]