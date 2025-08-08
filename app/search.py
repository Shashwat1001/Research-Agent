import os, requests
from typing import List, Dict
from .utils import getenv_str, log, sha1, load_cache, save_cache

SERP_API = "https://serpapi.com/search.json"

def search_web(query: str, k: int = 6) -> List[Dict]:
    """Return a list of dicts: {title, url, snippet} via SerpAPI."""
    api_key = getenv_str("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_KEY not set")

    cache_key = f"serp_{sha1(query)}_{k}"
    cached = load_cache(cache_key)
    if cached:
        return cached["items"]

    params = {
        "engine": "google",
        "q": query,
        "num": k,
        "api_key": api_key,
    }
    log(f"[search] {query}")
    r = requests.get(SERP_API, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    organic = data.get("organic_results", [])[:k]
    items = [{
        "title": it.get("title"),
        "url": it.get("link"),
        "snippet": it.get("snippet")
    } for it in organic if it.get("link")]
    save_cache(cache_key, {"items": items})
    return items
