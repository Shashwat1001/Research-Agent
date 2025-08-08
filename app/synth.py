from typing import List, Dict
from .utils import domain

def build_source_snippets(raw_chunks: List[Dict], max_sources: int = 10) -> List[Dict]:
    """Convert chunks [(chunk, url, score, title)] -> compact list with IDs and merged snippets per url/domain."""
    # Keep top by score and ensure domain diversity
    out = []
    seen_domains = set()
    sid = 1
    for ch in raw_chunks:
        chunk, url, score, title = ch["chunk"], ch["url"], ch["score"], ch["title"]
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
