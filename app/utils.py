import os
import time
import hashlib
import json
from typing import Any, Dict, Iterable, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()

def now_ts() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

def log(msg: str):
    print(f"[{now_ts()}] {msg}", flush=True)

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)

def cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")

def load_cache(key: str) -> Optional[Dict[str, Any]]:
    path = cache_path(key)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_cache(key: str, data: Dict[str, Any]):
    path = cache_path(key)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log(f"Cache save error: {e}")

def getenv_str(name: str, default: str = "") -> str:
    val = os.getenv(name, default)
    return val if val is not None else default

def getenv_int(name: str, default: int) -> int:
    v = os.getenv(name)
    try:
        return int(v) if v is not None else default
    except Exception:
        return default

def dedupe_by(items: Iterable[dict], key="url") -> List[dict]:
    seen = set()
    out = []
    for it in items:
        k = it.get(key)
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out

def domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""

def dedupe_by_domain(items: Iterable[dict], key="url") -> List[dict]:
    seen = set()
    out = []
    for it in items:
        u = it.get(key, "")
        d = domain(u)
        if d and d not in seen:
            seen.add(d)
            out.append(it)
    return out
