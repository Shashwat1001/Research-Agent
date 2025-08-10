# app/agent.py
from typing import Dict, List
import os

from .utils import log, dedupe_by, dedupe_by_domain
from .search import search_web
from .fetch import fetch_and_extract
from .chunk import (
    chunk_text,
    rank_chunks,
    rerank_serp_by_embedding,
    rerank_chunks_by_embedding,
)
from .llm import (
    plan_queries,
    synthesize_answer,
    critique_answer,
    embed_texts,  # embeddings for semantic re-ranking
)
from .synth import build_source_snippets


def _is_pdf(url: str) -> bool:
    """Heuristic to skip PDFs (can be heavy to fetch/parse)."""
    u = (url or "").lower()
    return u.endswith(".pdf") or "/pdf" in u or ".pdf?" in u


def answer(
    question: str,
    max_iters: int = 2,
    topk: int = 6,
    model: str = "gpt-4o-mini",
    safe_mode: bool = None,
) -> Dict:
    """
    Main agent loop:
      - plan queries
      - search (optionally across multiple engines)
      - fetch/parse & chunk (or use SERP snippets in safe_mode)
      - (optional) semantic re-ranking (SERP + chunks)
      - synthesize -> critique -> possibly re-plan
    Stops when confidence >= 0.75 or max_iters reached.

    Env flags:
      SAFE_MODE=1         -> default safe_mode True (do not fetch pages, use SERP snippets)
      RERANK_SERP=1       -> re-rank SERP results with embeddings before fetching
      RERANK_CHUNKS=1     -> re-rank chunks with embeddings after BM25
    """
    if safe_mode is None:
        safe_mode = os.getenv("SAFE_MODE", "0") == "1"

    use_rerank_serp = os.getenv("RERANK_SERP", "0") == "1"
    use_rerank_chunks = os.getenv("RERANK_CHUNKS", "0") == "1"

    log(f"Question: {question}")
    queries = plan_queries(question, model=model)

    # keep planner output bounded
    if len(queries) > 6:
        queries = queries[:6]

    known_chunks: List[Dict] = []

    for it in range(max_iters):
        log(f"--- Iteration {it+1}/{max_iters} ---")

        # 1) Search (respects SEARCH_ENGINES env inside search_web)
        results: List[Dict] = []
        for q in queries:
            results.extend(search_web(q, k=topk))

        # 2) Deduplicate & skip PDFs; keep domain diversity
        results = dedupe_by(results, key="url")
        results = [r for r in results if not _is_pdf(r.get("url", ""))]
        results = dedupe_by_domain(results, key="url")

        # 3) Optional SERP re-ranking (semantic) before any fetch
        if use_rerank_serp and results:
            try:
                results = rerank_serp_by_embedding(
                    question, results, embed_fn=lambda xs: embed_texts(xs)
                )
            except Exception as e:
                log(f"[rerank-serp] skipped due to error: {e}")

        # 4) Build candidate evidence
        if safe_mode:
            # Use search snippets only (very low RAM path)
            for r in results[:10]:
                snippet = (r.get("snippet") or "")[:1000]
                if not snippet:
                    continue
                known_chunks.append(
                    {
                        "chunk": snippet,
                        "url": r["url"],
                        "score": 1.0,  # flat score is fine for snippets
                        "title": r.get("title") or r["url"],
                    }
                )
        else:
            # Fetch & parse a small subset to avoid memory spikes
            pages_seen = 0
            for r in results:
                if pages_seen >= 8:  # hard cap on pages this iteration
                    break
                url = r["url"]
                try:
                    page = fetch_and_extract(url)
                except Exception as e:
                    log(f"[fetch-error] {url} :: {e}")
                    continue

                title = page.get("title") or url
                text = page.get("text") or ""
                if not text:
                    continue

                # Chunk & lexical rank (BM25)
                chunks = chunk_text(text, chunk_size=900, overlap=120)
                scored = rank_chunks(chunks, question, topn=2)  # keep small per page
                for chunk, score in scored:
                    known_chunks.append(
                        {"chunk": chunk, "url": url, "score": float(score), "title": title}
                    )
                pages_seen += 1

        # 5) Optional chunk re-ranking (semantic) after BM25
        if use_rerank_chunks and known_chunks:
            try:
                bm25_texts = [kc["chunk"] for kc in known_chunks]
                top_texts = rerank_chunks_by_embedding(
                    question,
                    bm25_texts,
                    embed_fn=lambda xs: embed_texts(xs),
                    topn=24,
                )
                keep = set(top_texts)
                known_chunks = [kc for kc in known_chunks if kc["chunk"] in keep][:24]
            except Exception as e:
                log(f"[rerank-chunks] skipped due to error: {e}")

        # Final cap (keeps behavior stable if re-rank is off)
        known_chunks = sorted(known_chunks, key=lambda x: x["score"], reverse=True)[:24]

        # 6) Trim to source list (domain-diverse) for the LLM
        raw = [
            {"chunk": c["chunk"], "url": c["url"], "score": c["score"], "title": c["title"]}
            for c in known_chunks
        ]
        sources = build_source_snippets(raw, max_sources=8)

        # 7) Synthesize & critique
        draft = synthesize_answer(question, sources, model=model)
        critique = critique_answer(question, draft.get("answer", ""), model=model)

        log(
            f"Critique confidence: {critique.get('confidence')} "
            f"| gaps: {len(critique.get('gaps', []))}"
        )

        # 8) Stop or iterate
        if critique.get("confidence", 0.0) >= 0.75 or it == max_iters - 1:
            return {
                "answer": draft.get("answer", ""),
                "citations": draft.get("citations", []),
                "confidence": critique.get("confidence", 0.0),
                "gaps": critique.get("gaps", []),
            }

        # Re-plan using the critic's gaps
        gap_text = " | ".join(critique.get("gaps", [])) or "Expand on counterpoints and recency"
        queries = plan_queries(f"{question}\nFocus on: {gap_text}", model=model)

    # Fallback
    return {
        "answer": "Unable to reach high confidence.",
        "citations": [],
        "confidence": 0.5,
        "gaps": [],
    }
