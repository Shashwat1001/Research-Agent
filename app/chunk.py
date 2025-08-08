import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi

def normalize(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 150) -> List[str]:
    text = normalize(text)
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

def rank_chunks(chunks: List[str], query: str, topn: int = 6) -> List[Tuple[str, float]]:
    if not chunks:
        return []
    # simple tokenization
    corpus = [c.split() for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.split())
    scored = list(zip(chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:topn]
