"""End-to-end smoke test for the newspaper agent.

Run with:  python scripts/test_agent.py

Hits OpenRouter (LLM) and Tavily (search) for real, twice — once for
general news, once for tech. Validates that the returned NewsResponse
honors the schema constraints (1-5 sources, non-empty summary, https URLs).
"""

from __future__ import annotations

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import run_news_agent  # noqa: E402
from app.schemas import NewsCategory, NewsResponse  # noqa: E402


def _check(response: NewsResponse, label: str) -> bool:
    print(f"\n=== {label} ===")
    print(f"Summary ({len(response.summary)} chars):")
    print(f"  {response.summary}")
    print(f"\nSources ({len(response.sources)}):")
    for i, url in enumerate(response.sources, 1):
        print(f"  {i}. {url}")

    ok = True
    if not (1 <= len(response.sources) <= 5):
        print(f"[FAIL] sources count out of range: {len(response.sources)}")
        ok = False
    if not response.summary.strip():
        print("[FAIL] summary is empty")
        ok = False
    for url in response.sources:
        if not str(url).startswith(("http://", "https://")):
            print(f"[FAIL] non-http url: {url}")
            ok = False
    if ok:
        print(f"[OK] {label} passed schema checks")
    return ok


async def main() -> int:
    results: list[bool] = []

    print("\n[1/2] Calling run_news_agent(category=None)")
    print("-" * 60)
    try:
        response = await run_news_agent(category=None)
        results.append(_check(response, "General news"))
    except Exception:
        print("[FAIL] general-news call raised:")
        traceback.print_exc()
        results.append(False)

    print("\n[2/2] Calling run_news_agent(category=NewsCategory.TECH)")
    print("-" * 60)
    try:
        response = await run_news_agent(category=NewsCategory.TECH)
        results.append(_check(response, "Tech news"))
    except Exception:
        print("[FAIL] tech-news call raised:")
        traceback.print_exc()
        results.append(False)

    passed = sum(results)
    print("\n" + "=" * 60)
    print(f"{passed}/{len(results)} agent calls passed")
    if passed == len(results):
        print("[OK] Agent test passed")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
