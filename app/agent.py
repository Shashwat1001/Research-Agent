from typing import Dict, List
import os
from .utils import log, dedupe_by, dedupe_by_domain
from .search import search_web
from .fetch import fetch_and_extract
from .chunk import chunk_text, rank_chunks
from .llm import plan_queries, synthesize_answer, critique_answer
from .synth import build_source_snippets

def _is_pdf(url: str) -> bool:
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
    safe_mode=True -> DO NOT fetch pages; synthesize from search snippets only (very low RAM).
    Default is read from env SAFE_MODE (1/0), falls back to False.
    """
    if safe_mode is None:
        safe_mode = os.getenv("SAFE_MODE", "0") == "1"

    log(f"Question: {question}")
    queries = plan_queries(question, model=model)

    # keep only small # of queries in case planner returns many
    if len(queries) > 6:
        queries = queries[:6]

    known_chunks: List[Dict] = []

    for it in range(max_iters):
        log(f"--- Iteration {it+1}/{max_iters} ---")

        # 1) Search
        results = []
        for q in queries:
            results.extend(search_web(q, k=topk))

        # 2) Deduplicate & skip PDFs
        results = dedupe_by(results, key="url")
        results = [r for r in results if not _is_pdf(r.get("url", ""))]
        results = dedupe_by_domain(results, key="url")

        if safe_mode:
            # 3A) SAFE MODE: don't fetch pages; just use search snippets
            #    Build a pseudo "chunk list" from SERP snippets (very low memory)
            for i, r in enumerate(results[:10], start=1):
                snippet = (r.get("snippet") or "")[:1000]
                if not snippet:
                    continue
                known_chunks.append({
                    "chunk": snippet,
                    "url": r["url"],
                    "score": 1.0,                 # flat score is OK for snippets
                    "title": r.get("title") or r["url"]
                })

        else:
            # 3B) NORMAL MODE: fetch & extract, but guarded
            pages_seen = 0
            for r in results:
                if pages_seen >= 8:      # hard cap to avoid memory spikes
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

                chunks = chunk_text(text, chunk_size=900, overlap=120)
                # rank and keep only top 2 chunks per page (reduce RAM)
                scored = rank_chunks(chunks, question, topn=2)
                for chunk, score in scored:
                    known_chunks.append({"chunk": chunk, "url": url, "score": float(score), "title": title})
                pages_seen += 1

        # Keep top 24 across everything
        known_chunks = sorted(known_chunks, key=lambda x: x["score"], reverse=True)[:24]

        # Build compact sources (ensure diversity)
        # When safe_mode=True, this will use SERP snippets as "sources"
        raw = [{"chunk": c["chunk"], "url": c["url"], "score": c["score"], "title": c["title"]} for c in known_chunks]
        sources = build_source_snippets(raw, max_sources=8)

        draft = synthesize_answer(question, sources, model=model)
        critique = critique_answer(question, draft.get("answer", ""), model=model)

        log(f"Critique confidence: {critique.get('confidence')} | gaps: {len(critique.get('gaps', []))}")
        if critique.get("confidence", 0.0) >= 0.75 or it == max_iters - 1:
            return {
                "answer": draft.get("answer", ""),
                "citations": draft.get("citations", []),
                "confidence": critique.get("confidence", 0.0),
                "gaps": critique.get("gaps", []),
            }

        # Re-plan based on gaps
        gap_text = " | ".join(critique.get("gaps", [])) or "Expand on counterpoints and recency"
        queries = plan_queries(f"{question}\nFocus on: {gap_text}", model=model)

    return {"answer": "Unable to reach high confidence.", "citations": [], "confidence": 0.5, "gaps": []}
