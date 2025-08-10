# Agentic Research Assistant — CLI + MCP Tool + Streamlit UI
# 🔍 Agentic Research Assistant

An autonomous research agent that:
- Formulates diverse search queries for a user’s question.
- Executes web searches via **SerpAPI** (Google Search).
- Fetches and processes page text.
- Iteratively refines queries based on gaps in knowledge.
- Synthesizes a concise, well-cited answer.
- (Optional) **Re-ranks** sources and text chunks using semantic embeddings.

## ✨ Features
- **Three modes**:
  1. **CLI** – run from terminal
  2. **MCP tool** – integrates into your existing MCP server
  3. **Streamlit UI** – browser-based interface
- **Safe Mode** – skip page fetching (uses search snippets only) for speed and stability.
- **Re-ranking** – (optional) improve relevance via semantic embeddings.
- **Auto-Fallback** – if embedding quota is exceeded, falls back to BM25 ranking automatically.

---

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # then edit .env
```

**.env**
```
OPENAI_API_KEY=sk-...
SERPAPI_KEY=YOUR_SERP_API_KEY
# Optional:
SAFE_MODE=0           # 1 = don't fetch pages (uses search snippets only)
MAX_HTML_BYTES=1500000
DEFAULT_LLM=openai:gpt-4o-mini
MAX_ITERS=2
TOPK=6
```

## 1) Run the CLI

```bash
# from project root, with venv activated and .env filled
# Recommended first: Safe Mode + re-ranking ON
export RERANK_SERP=1
export RERANK_CHUNKS=1
export SEARCH_ENGINES=serpapi,tavily   # or just "serpapi" if you don't have Tavily key yet
python -m app.main "What are the main causes and potential solutions for global plastic pollution?" --safe-mode

python -m app.main "What are the main causes and potential solutions for global plastic pollution?"
# Safer on low-RAM:
python -m app.main "Compare the economic impacts of solar vs fossil fuels." --safe-mode
```

## 2) Run Streamlit UI

```bash
export RERANK_SERP=1
export RERANK_CHUNKS=1
export SEARCH_ENGINES=serpapi,tavily
streamlit run streamlit_app.py
# open http://localhost:8501

```

## 3) Use MCP Tool

### 3a) Quick test with the minimal stdio server
Terminal A:
```bash
python server_mcp.py
```
Terminal B (send JSON lines):
```bash
printf '%s\n' '{"type":"initialize"}' '{"type":"list_tools"}' '{"type":"call_tool","tool":"agentic_research","params":{"question":"Causes of plastic pollution?","safe_mode":true}}' | python server_mcp.py
```

### 3b) Integrate into your existing MCP server
In your `src/mcp_server/server.py`:
```python
from app.tools.research_tool import MCP_TOOL as RESEARCH_TOOL
TOOLS_REGISTRY.append(RESEARCH_TOOL)
```
Ensure your server supports:
- listing tools (names + parameters)
- dispatching `call_tool` to `handler(params)` and returning JSON

## Notes
- If processes get killed, start with `--safe-mode` or set `SAFE_MODE=1`.
- Lower memory by reducing `TOPK`, `MAX_ITERS`, or `MAX_HTML_BYTES` (e.g., 800000).
- Respect site terms/robots when fetching pages.
