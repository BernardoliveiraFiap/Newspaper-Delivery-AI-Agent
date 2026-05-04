"""Agent tools.

This module is the agent's only window onto the outside world: every
external lookup it makes goes through Tavily Search. We rely on Tavily's
native filters (``topic="news"``, ``days=2``) rather than fetching a
broad result set and post-filtering — pushing the constraint to the
provider is both cheaper and more reliable than reproducing it locally.

Note on ``days`` (langchain-tavily 0.2.18): the wrapper does not expose
``days`` as a constructor field, but the underlying Tavily REST API
supports it for the ``news`` topic and the wrapper passes unknown
kwargs through verbatim. We use a thin subclass to inject it on every
call so the "last 2 days" requirement is enforced at the source.
"""

from typing import Any

from langchain_tavily import TavilySearch

from app.config import settings

NEWS_LOOKBACK_DAYS = 2


class _NewsTavilySearch(TavilySearch):
    """``TavilySearch`` that always restricts results to the last N days."""

    def _run(self, query: str, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("days", NEWS_LOOKBACK_DAYS)
        return super()._run(query, **kwargs)

    async def _arun(self, query: str, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("days", NEWS_LOOKBACK_DAYS)
        return await super()._arun(query, **kwargs)


def get_news_search_tool() -> TavilySearch:
    """Build the Tavily news-search tool used by the agent.

    Parameter choices:
      * ``max_results=8`` — we deliberately fetch more than the 5-source
        cap on the API response so the LLM can curate the best 5 from a
        wider candidate set instead of being forced to take whatever the
        first call returned.
      * ``topic="news"`` — restrict to news publishers; ``general`` would
        let blogs and forums leak in.
      * ``search_depth="advanced"`` — Tavily's higher-quality (and slower)
        retrieval mode; the latency hit is worth it for a once-per-request
        agent call.
      * ``include_answer=False`` — Tavily can return its own synthesized
        answer, but our agent owns the summary; we want raw articles only.
      * ``days`` — injected by ``_NewsTavilySearch`` (see module docstring).
    """
    return _NewsTavilySearch(
        max_results=8,
        topic="news",
        search_depth="advanced",
        include_answer=False,
        tavily_api_key=settings.TAVILY_API_KEY,
    )
