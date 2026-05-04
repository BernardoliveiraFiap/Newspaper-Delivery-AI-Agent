"""LangChain agent orchestration.

Combines the OpenRouter LLM (``app.llm``) with the Tavily news search
tool (``app.tools``) using ``langchain.agents.create_agent`` and asks
for ``NewsResponse`` as a structured output. The agent decides on a
search query, calls the tool, picks the best sources, and writes a
plain-language summary — all in one ``ainvoke`` call.
"""

from __future__ import annotations

import logging

from langchain.agents import create_agent

from app.llm import get_llm
from app.schemas import NewsCategory, NewsResponse
from app.tools import get_news_search_tool

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a newspaper delivery agent.

Your job is to find the most important news from the last 2 days and
deliver them to the reader as a short, easy-to-read briefing.

## How to work

1. Decide on a clear search query based on the user's request:
   - If the user asks for "general" or unspecified news, search for
     world headlines (e.g. "biggest world news headlines today").
   - If the user asks for a specific category, translate it into a
     natural news query, do NOT just echo the word back. Examples:
       * tech       -> "biggest technology news today"
       * economics  -> "major economic and markets news today"
       * politics   -> "major political news today"
2. Call the news search tool exactly once with that query. The tool
   already restricts results to the last 2 days; do not try to filter
   by date yourself.
3. From the tool results, pick between 1 and 5 of the strongest
   stories. Curation rules:
   - Prefer DIVERSE publishers — never return five links from the
     same site. Aim for at least 3 different domains when possible.
   - Prefer headlines that look informative and recent over vague
     or clickbait ones.
   - Drop near-duplicates (multiple outlets covering the exact same
     story with the same angle) — keep only the clearest one.
   - If the tool returns nothing useful, still produce a short
     summary explaining that and select whichever 1 source is the
     closest match.
4. Write ONE paragraph (3 to 6 sentences) summarizing what is
   happening across the picked stories.

## Tone

Plain, simple English. No jargon, no specialist vocabulary, no
business / financial / tech buzzwords. Write so any reader, with no
background in the topic, can understand on the first read. Stay
neutral and factual — no opinion, no speculation.

## Hard constraints

- The window is "the last 2 days" — never reference older events.
- Return between 1 and 5 source URLs, never more than 5.
- The summary must not be empty.
- Source URLs must come from the tool results; never invent URLs.
"""


_USER_MESSAGE_TEMPLATES: dict[NewsCategory | None, str] = {
    None: "Please find and summarize the most important general news from the last 2 days.",
    NewsCategory.TECH: (
        "Please find and summarize the most important technology news from the last 2 days."
    ),
    NewsCategory.ECONOMICS: (
        "Please find and summarize the most important economics and markets news "
        "from the last 2 days."
    ),
    NewsCategory.POLITICS: (
        "Please find and summarize the most important political news from the last 2 days."
    ),
}


def _build_user_message(category: NewsCategory | None) -> str:
    return _USER_MESSAGE_TEMPLATES[category]


def _build_agent():
    return create_agent(
        model=get_llm(),
        tools=[get_news_search_tool()],
        system_prompt=SYSTEM_PROMPT,
        response_format=NewsResponse,
    )


async def run_news_agent(category: NewsCategory | None) -> NewsResponse:
    """Run the newspaper agent and return a validated ``NewsResponse``.

    Raises:
        RuntimeError: if the agent runs but does not produce a valid
            structured ``NewsResponse`` (e.g. the model failed to follow
            the schema, or the underlying APIs errored).
    """
    user_message = _build_user_message(category)
    logger.info("Running news agent (category=%s)", category)

    agent = _build_agent()

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]}
        )
    except Exception as exc:
        raise RuntimeError(f"Agent failed to run: {exc}") from exc

    structured = result.get("structured_response")
    if not isinstance(structured, NewsResponse):
        raise RuntimeError(
            "Agent did not return a valid NewsResponse "
            f"(got type={type(structured).__name__})."
        )
    return structured
