from typing import List, Dict
from .utils import domain

def build_source_snippets(raw_chunks: List[Dict], max_sources: int = 8) -> List[Dict]:
    """Convert chunks -> compact list with IDs and merged snippets per domain for diversity."""
    out = []
    seen_domains = set()
    sid = 1
    for ch in raw_chunks:
        chunk, url, title = ch["chunk"], ch["url"], ch["title"]
        d = domain(url)
        if d in seen_domains:
            continue
        seen_domains.add(d)
        out.append({
            "id": f"S{sid}",
            "url": url,
            "title": title,
            "snippet": chunk
        })
        sid += 1
        if len(out) >= max_sources:
            break
    return out
