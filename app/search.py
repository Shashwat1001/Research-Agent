import requests, os
from typing import List, Dict
from .utils import getenv_str, log, sha1, load_cache, save_cache, dedupe_by_domain

SERP_API = "https://serpapi.com/search.json"
TAVILY_API = "https://api.tavily.com/search"

def _search_serpapi(query: str, k: int) -> List[Dict]:
    api_key = getenv_str("SERPAPI_KEY")
    if not api_key:
        return []
    params = {"engine": "google", "q": query, "num": k, "api_key": api_key}
    log(f"[search:serpapi] {query}")
    r = requests.get(SERP_API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    organic = data.get("organic_results", [])[:k]
    return [{"title": it.get("title"),
             "url": it.get("link"),
             "snippet": it.get("snippet")} for it in organic if it.get("link")]

def _search_tavily(query: str, k: int) -> List[Dict]:
    api_key = getenv_str("TAVILY_API_KEY")
    if not api_key:
        return []
    log(f"[search:tavily] {query}")
    r = requests.post(TAVILY_API, json={"api_key": api_key, "query": query, "max_results": k}, timeout=30)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])[:k]
    return [{"title": it.get("title"),
             "url": it.get("url"),
             "snippet": it.get("content")} for it in results if it.get("url")]

def search_web(query: str, k: int = 6) -> List[Dict]:
    engines = getenv_str("SEARCH_ENGINES", "serpapi").split(",")
    engines = [e.strip().lower() for e in engines if e.strip()]
    cache_key = f"search_{sha1('|'.join(engines)+query)}_{k}"
    cached = load_cache(cache_key)
    if cached:
        return cached["items"]

    items: List[Dict] = []
    if "serpapi" in engines:
        items += _search_serpapi(query, k)
    if "tavily" in engines:
        items += _search_tavily(query, k)

    # merge unique by URL, then dedupe by domain for diversity
    seen = set()
    merged = []
    for it in items:
        u = it.get("url")
        if u and u not in seen:
            seen.add(u)
            merged.append(it)

    merged = dedupe_by_domain(merged, key="url")
    save_cache(cache_key, {"items": merged})
    return merged
