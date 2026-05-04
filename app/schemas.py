"""Pydantic request/response models for the API."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class NewsCategory(str, Enum):
    """Optional category filter applied to the news search."""

    TECH = "tech"
    ECONOMICS = "economics"
    POLITICS = "politics"


class NewsRequest(BaseModel):
    """Request body for the newspaper agent endpoint."""

    category: NewsCategory | None = Field(
        default=None,
        description="Optional category filter. When omitted, the agent fetches general top news.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"category": "tech"},
                {},
            ]
        }
    )


class NewsResponse(BaseModel):
    """Response body returned by the newspaper agent endpoint."""

    summary: str = Field(
        ...,
        min_length=1,
        description="Plain-language summary of recent news.",
    )
    sources: list[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Source URLs backing the summary (between 1 and 5).",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": (
                        "Over the past two days, major tech companies announced new AI "
                        "products and several regulatory developments emerged in the EU."
                    ),
                    "sources": [
                        "https://example-news.com/article-1",
                        "https://example-news.com/article-2",
                    ],
                }
            ]
        }
    )
