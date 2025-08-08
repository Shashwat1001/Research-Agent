from typing import Dict, List, Any
import json
from .utils import getenv_str, log
from openai import OpenAI

def _client():
    api_key = getenv_str("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)

def _chat(model: str, system: str, user: str, response_format: str = "json_object", temperature: float = 0.2) -> str:
    client = _client()
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        response_format={"type": response_format},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    return resp.choices[0].message.content

def plan_queries(question: str, model: str) -> List[str]:
    system = "You create diverse, high-coverage web search queries in English."
    user = f"""User question:
{question}

Produce 4-8 diverse search queries covering subtopics, synonyms, and contrasting views.
Return JSON: {{"queries": ["...", "..."]}}"""
    out = _chat(model, system, user, "json_object", temperature=0.2)
    try:
        data = json.loads(out)
        queries = data.get("queries", [])
        return [q for q in queries if isinstance(q, str) and q.strip()]
    except Exception as e:
        log(f"[plan_queries] parse error: {e}; raw: {out}")
        return [question]

def synthesize_answer(question: str, sources: List[dict], model: str) -> Dict[str, Any]:
    system = "You write concise, neutral, well-cited syntheses using only provided sources."
    src_lines = []
    for s in sources:
        sid = s.get("id"); url = s.get("url"); snip = s.get("snippet","")[:1200]
        src_lines.append(f"[{sid}] {url}\n{snip}")
    src_block = "\n\n".join(src_lines)

    user = f"""Question: {question}

You are given SOURCES as (id, url, snippet). Use only these sources; paraphrase claims and add inline citations like [S1].
Ensure every paragraph has at least one citation. Keep it factual and balanced.
SOURCES:
{src_block}

Return JSON:
{{"answer":"...", "citations":[{{"id":"S1","url":"...","title":"..."}}, ...]}}"""
    out = _chat(model, system, user, "json_object", temperature=0.4)
    try:
        data = json.loads(out)
        return data
    except Exception as e:
        log(f"[synthesize_answer] parse error: {e}; raw: {out}")
        return {"answer": "Failed to synthesize.", "citations": []}

def critique_answer(question: str, answer: str, model: str) -> Dict[str, Any]:
    system = "You critically review answers for coverage, sourcing, contradictions."
    user = f"""Question: {question}
Answer:
\"\"\"
{answer}
\"\"\"

Provide a confidence (0–1), and list gaps (missing subtopics, weak sourcing, contradictions).
Return JSON: {{"confidence": 0.0, "gaps": ["...", "..."]}}"""
    out = _chat(model, system, user, "json_object", temperature=0.0)
    try:
        return json.loads(out)
    except Exception:
        return {"confidence": 0.5, "gaps": ["Could not parse critique."]}
