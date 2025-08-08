# Agentic Research Assistant — CLI + MCP Tool + Streamlit UI

This bundle includes:
- **CLI** (`python -m app.main "question"`)
- **MCP tool** (`app/tools/research_tool.py`) + **minimal stdio server** (`server_mcp.py`) for testing
- **Streamlit UI** (`streamlit_app.py`) for a simple browser app

## 0) Setup

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
python -m app.main "What are the main causes and potential solutions for global plastic pollution?"
# Safer on low-RAM:
python -m app.main "Compare the economic impacts of solar vs fossil fuels." --safe-mode
```

## 2) Run Streamlit UI

```bash
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
