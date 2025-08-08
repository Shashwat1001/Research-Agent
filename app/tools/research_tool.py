from app.agent import answer

def research_tool_handler(params: dict) -> dict:
    """
    MCP tool handler for the research assistant.
    Expects params: {"question": str, "max_iters": int, "topk": int, "model": str, "safe_mode": bool}
    """
    question = params.get("question")
    if not question:
        return {"error": "Missing 'question' parameter"}

    max_iters = int(params.get("max_iters", 2))
    topk = int(params.get("topk", 6))
    model = params.get("model", "gpt-4o-mini")
    safe_mode = bool(params.get("safe_mode", False))

    result = answer(
        question=question,
        max_iters=max_iters,
        topk=topk,
        model=model,
        safe_mode=safe_mode
    )
    return {"result": result}

MCP_TOOL = {
    "name": "agentic_research",
    "description": "Run the Agentic Research Assistant for complex open-ended questions.",
    "handler": research_tool_handler,
    "parameters": [
        {"name": "question", "type": "string", "required": True, "description": "Research question"},
        {"name": "max_iters", "type": "integer", "required": False, "description": "Max search iterations"},
        {"name": "topk", "type": "integer", "required": False, "description": "Top results per query"},
        {"name": "model", "type": "string", "required": False, "description": "LLM model"},
        {"name": "safe_mode", "type": "boolean", "required": False, "description": "Skip page fetching if True"},
    ]
}
