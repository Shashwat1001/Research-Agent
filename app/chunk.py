import re
from typing import List, Tuple
from rank_bm25 import BM25Okapi
from typing import Dict, List
from math import sqrt

def normalize(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
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
    corpus = [c.split() for c in chunks]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.split())
    scored = list(zip(chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:topn]

def _cos(a, b):
    num = sum(x*y for x, y in zip(a, b))
    da = sqrt(sum(x*x for x in a))
    db = sqrt(sum(y*y for y in b))
    return 0.0 if (da == 0 or db == 0) else num / (da * db)

def rerank_serp_by_embedding(question: str, serp_items: List[Dict], embed_fn) -> List[Dict]:
    """
    Reorder SERP items by cosine similarity between (title+snippet) and the question.
    embed_fn: callable that takes list[str] -> list[list[float]] (embeddings)
    """
    if not serp_items:
        return serp_items
    q_emb = embed_fn([question])[0]
    texts = [f"{it.get('title','')} {it.get('snippet','')}" for it in serp_items]
    embs = embed_fn(texts)
    scored = [(it, _cos(q_emb, e)) for it, e in zip(serp_items, embs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [it for it, _ in scored]

def rerank_chunks_by_embedding(question: str, chunks: List[str], embed_fn, topn: int = 24) -> List[str]:
    """
    Reorder chunk texts by cosine similarity to question; return topn chunk strings.
    """
    if not chunks:
        return []
    q_emb = embed_fn([question])[0]
    embs = embed_fn(chunks)
    scored = list(zip(chunks, (_cos(q_emb, e) for e in embs)))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:topn]]
