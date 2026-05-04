"""LLM client factory.

Why OpenRouter via ``ChatOpenAI``: OpenRouter exposes an OpenAI-compatible
API, so we can reuse the OpenAI LangChain integration just by overriding
``base_url``. No custom client / no extra adapter needed.
"""

from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm() -> ChatOpenAI:
    """Build a fresh ``ChatOpenAI`` instance pointed at OpenRouter.

    A factory (rather than a module-level singleton) keeps each caller /
    test free to construct its own client, and makes mocking trivial.

    Defaults:
      * ``temperature=0.2`` — news summarization is a factual task; we
        want stable, low-variance output, not creative writing. The
        model and base_url come from settings, but temperature is a
        product decision and lives here. If we ever want to tune it
        without redeploying we can promote it to an env var.
      * ``timeout=60`` — guards against an HTTP hang stalling a request.
      * ``max_retries=2`` — OpenRouter routes to many upstream providers;
        a small retry smooths over transient blips without masking real
        outages.
    """
    return ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=0.2,
        timeout=60,
        max_retries=2,
    )
