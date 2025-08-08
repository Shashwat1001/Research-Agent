#!/usr/bin/env python3
import sys, json
from app.tools.research_tool import MCP_TOOL

TOOLS = {MCP_TOOL["name"]: MCP_TOOL}

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()

def handle(msg):
    mtype = msg.get("type")
    if mtype == "initialize":
        return {"type": "initialized", "tools": [
            {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
            for t in TOOLS.values()
        ]}
    if mtype == "list_tools":
        return {"type": "tools", "tools": [
            {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
            for t in TOOLS.values()
        ]}
    if mtype == "call_tool":
        name = msg.get("tool")
        params = msg.get("params", {})
        tool = TOOLS.get(name)
        if not tool:
            return {"type": "error", "error": f"Unknown tool: {name}"}
        try:
            out = tool["handler"](params)
            return {"type": "tool_result", "tool": name, "result": out}
        except Exception as e:
            return {"type": "error", "error": f"{type(e).__name__}: {e}"}
    return {"type": "error", "error": "Unknown message type"}

def main():
    send({"type": "ready"})
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception as e:
            send({"type": "error", "error": f"invalid json: {e}"})
            continue
        resp = handle(msg)
        send(resp)

if __name__ == "__main__":
    main()
