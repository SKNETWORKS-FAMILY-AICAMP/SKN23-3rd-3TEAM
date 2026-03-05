import os
import requests
from typing import List, Dict

def web_search(query: str, k: int = 5) -> List[Dict]:
    provider = os.getenv("WEB_SEARCH_PROVIDER", "tavily")

    if provider == "tavily":
        api_key = os.getenv("TAVILY_API_KEY", "")
        assert api_key, "TAVILY_API_KEY missing"
        r = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "max_results": k},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        # tavily: results=[{title,url,content,...}]
        out = []
        for item in data.get("results", [])[:k]:
            out.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:500],
            })
        return out

    raise ValueError(f"Unsupported provider={provider}")