"""Live smoke tests for the LLM client and Tavily tool.

Run with:  python scripts/smoke_test.py

Hits the real OpenRouter and Tavily APIs using credentials from .env,
so it costs a fraction of a cent and a few seconds. Useful for the
graders to confirm the keys work before exercising the full agent.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Allow running as `python scripts/smoke_test.py` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage  # noqa: E402

from app.llm import get_llm  # noqa: E402
from app.tools import get_news_search_tool  # noqa: E402


def test_llm() -> bool:
    print("\n[1/2] LLM smoke test (OpenRouter)")
    print("-" * 50)
    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content="Reply with the single word: PONG")])
        print(f"Model reply: {response.content!r}")
        print("[OK] LLM call succeeded")
        return True
    except Exception:
        print("[FAIL] LLM call raised:")
        traceback.print_exc()
        return False


def test_tavily() -> bool:
    print("\n[2/2] Tavily smoke test")
    print("-" * 50)
    try:
        tool = get_news_search_tool()
        raw = tool.invoke({"query": "latest world news"})
        results = raw.get("results", []) if isinstance(raw, dict) else []
        print(f"Result count: {len(results)}")
        for i, item in enumerate(results[:3], 1):
            title = item.get("title", "<no title>")
            url = item.get("url", "<no url>")
            print(f"  {i}. {title}\n     {url}")
        print("[OK] Tavily call succeeded")
        return True
    except Exception:
        print("[FAIL] Tavily call raised:")
        traceback.print_exc()
        return False


def main() -> int:
    results = [test_llm(), test_tavily()]
    passed = sum(results)
    print("\n" + "=" * 50)
    print(f"{passed}/{len(results)} smoke tests passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
