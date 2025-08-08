import os
import requests, trafilatura
from typing import Dict
from .utils import log, sha1, load_cache, save_cache

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0; +https://example.org/bot)"
}

MAX_HTML_BYTES = int(os.getenv("MAX_HTML_BYTES", "1500000"))  # ~1.5 MB cap

def _is_html(content_type: str) -> bool:
    if not content_type:
        return True
    ct = content_type.lower()
    return ("text/html" in ct) or ("application/xhtml+xml" in ct)

def _download_capped(url: str) -> str:
    with requests.get(url, headers=HEADERS, timeout=45, stream=True) as r:
        r.raise_for_status()
        if not _is_html(r.headers.get("Content-Type", "")):
            raise ValueError(f"Non-HTML content-type: {r.headers.get('Content-Type','')}")
        clen = r.headers.get("Content-Length")
        if clen:
            try:
                if int(clen) > MAX_HTML_BYTES:
                    raise ValueError(f"Content too large: {clen} bytes")
            except Exception:
                pass
        buf = bytearray()
        for chunk in r.iter_content(chunk_size=65536):
            if not chunk:
                continue
            buf.extend(chunk)
            if len(buf) > MAX_HTML_BYTES:
                raise ValueError(f"Content exceeded cap ({MAX_HTML_BYTES} bytes)")
        enc = r.encoding or "utf-8"
        try:
            return buf.decode(enc, errors="ignore")
        except Exception:
            return buf.decode("utf-8", errors="ignore")

def fetch_and_extract(url: str) -> Dict:
    key = f"page_{sha1(url)}"
    cached = load_cache(key)
    if cached:
        return cached

    log(f"[fetch] {url}")
    html = _download_capped(url)

    data = None
    try:
        meta = trafilatura.bare_extraction(
            html,
            url=url,
            include_comments=False,
            favor_recall=True
        )
        if meta:
            data = {
                "url": url,
                "title": (meta.get("title") or url),
                "text": (meta.get("text") or "")
            }
    except Exception:
        data = None

    if not data or not data.get("text"):
        try:
            text = trafilatura.extract(html, include_comments=False) or ""
        except Exception:
            text = ""
        data = {"url": url, "title": url, "text": text}

    save_cache(key, data)
    return data
