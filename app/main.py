"""FastAPI application entrypoint.

Single endpoint: ``POST /news``. The endpoint validates the request via
``NewsRequest``, runs the LangChain agent, and returns a validated
``NewsResponse``. Swagger UI is served at ``/docs``.
"""

from fastapi import FastAPI, HTTPException

from app.agent import run_news_agent
from app.schemas import NewsRequest, NewsResponse

app = FastAPI(
    title="Newspaper Delivery AI Agent",
    description=(
        "Delivers a plain-language summary of the most important news from "
        "the last 2 days, along with up to 5 source links. Powered by a "
        "LangChain agent using OpenRouter (LLM) and Tavily (web search)."
    ),
    version="0.1.0",
)


@app.post(
    "/news",
    response_model=NewsResponse,
    tags=["news"],
    summary="Get the latest news summary",
    description=(
        "Triggers the newspaper agent to fetch news from the last 2 days "
        "via Tavily and produce a short, plain-language summary plus up to "
        "5 source URLs. The `category` field is optional — when omitted the "
        "agent returns general top headlines."
    ),
)
async def get_news(request: NewsRequest) -> NewsResponse:
    try:
        return await run_news_agent(request.category)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream agent failure: {exc}",
        ) from exc
