import argparse, os
from .agent import answer

def cli():
    p = argparse.ArgumentParser(description="Agentic Research Assistant (CLI)")
    p.add_argument("question", type=str, help="Your research question in quotes")
    p.add_argument("--max-iters", type=int, default=int(os.getenv("MAX_ITERS", "2")))
    p.add_argument("--topk", type=int, default=int(os.getenv("TOPK", "6")))
    p.add_argument("--model", type=str, default=os.getenv("DEFAULT_LLM", "openai:gpt-4o-mini"))
    p.add_argument("--safe-mode", action="store_true", help="Skip fetching pages; synthesize from search snippets only")
    args = p.parse_args()

    # Model name normalization: allow "openai:gpt-4o-mini" or just "gpt-4o-mini"
    model = args.model.split(":", 1)[-1]

    result = answer(
        args.question,
        max_iters=args.max_iters,
        topk=args.topk,
        model=model,
        safe_mode=args.safe_mode or (os.getenv("SAFE_MODE", "0") == "1"),
    )

    print("\n=== FINAL ANSWER ===\n")
    print(result.get("answer", ""))
    print("\n=== REFERENCES ===")
    for c in result.get("citations", []):
        print(f"- [{c.get('id')}] {c.get('title','')} :: {c.get('url','')}")
    print(f"\nConfidence: {result.get('confidence')}")
    if result.get("gaps"):
        print("Gaps:", "; ".join(result["gaps"]))

if __name__ == "__main__":
    cli()
