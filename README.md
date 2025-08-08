# Agentic Research Assistant (CLI)

A minimal, end-to-end **CLI** agent that:
1) Plans multiple search queries,
2) Searches the web (SerpAPI),
3) Fetches & cleans pages (trafilatura),
4) Chunks & ranks (BM25),
5) Synthesizes a cited answer (OpenAI),
6) Self-critiques and iterates if confidence is low.

## Quickstart

### 1) Python & keys
- Python 3.10+ recommended
- Create a virtualenv
- Install deps: `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and fill in your keys.

```
cp .env.example .env
# Edit .env to add:
# OPENAI_API_KEY=...
# SERPAPI_KEY=...
```

### 2) Run (CLI)
```
python -m app.main "What are the main causes and potential solutions for global plastic pollution?"
```

### 3) Flags
```
python -m app.main "your question" --max-iters 3 --topk 6 --model gpt-4o-mini
```

### 4) Output
- Streams logs to stdout
- Final answer printed with inline citations and a reference list

## Project Layout
```
app/
  agent.py        # control loop
  main.py         # CLI entry
  search.py       # SerpAPI wrapper
  fetch.py        # page fetch + clean
  chunk.py        # normalize, chunk, rank (BM25)
  llm.py          # OpenAI wrapper
  critique.py     # self-critique and gap extraction
  synth.py        # synthesis prompt builder
  utils.py        # caching, retries, helpers
requirements.txt
.env.example
README.md
```

## Notes
- This is a **skeleton**: safe defaults and defensive code are included.
- For PDFs, extend `fetch.py` with `pymupdf`/`pdfminer.six`.
- For multi-engine search, add a second client in `search.py` and merge results.
- Respect robots.txt and site terms when crawling. Use responsibly.
