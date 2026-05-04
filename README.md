# Newspaper Delivery AI Agent

A small FastAPI service that delivers a plain-language summary of the most
important news from the last 2 days, with up to 5 source links.

## Overview

The service exposes a single `POST /news` endpoint. Each request triggers
a LangChain agent that decides on a search query, calls the Tavily Search
API to fetch recent news articles, picks the most relevant sources, and
asks the LLM to write a short, easy-to-read briefing. The response is a
validated Pydantic model with the summary text and 1-5 source URLs. The
LLM provider is OpenRouter (model: `google/gemma-4-31b-it`); structured
output is enforced via `create_agent`'s `response_format`, so the agent
returns a `NewsResponse` directly — no manual JSON parsing.

## Stack

- **Python 3.12**
- **FastAPI** — HTTP layer, automatic Swagger UI at `/docs`
- **Pydantic v2** + **pydantic-settings** — request / response validation and config
- **LangChain 1.x** — `langchain.agents.create_agent` with structured output
- **OpenRouter** (via `langchain-openai`, OpenAI-compatible API) — LLM provider, model `google/gemma-4-31b-it`
- **Tavily Search API** (via `langchain-tavily`) — news retrieval, restricted to the last 2 days

## Project structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app + POST /news endpoint
│   ├── schemas.py      # NewsCategory, NewsRequest, NewsResponse
│   ├── agent.py        # create_agent + system prompt + run_news_agent
│   ├── tools.py        # Tavily search tool with days=2 injection
│   ├── llm.py          # ChatOpenAI factory pointed at OpenRouter
│   └── config.py       # pydantic-settings Settings + get_settings()
├── scripts/
│   ├── smoke_test.py   # real LLM + Tavily ping (no agent)
│   └── test_agent.py   # full agent end-to-end (general + tech)
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Setup

1. Clone the repo.
2. Create and activate a Python 3.12 virtual environment:

   ```
   python -m venv .venv
   .venv\Scripts\Activate.ps1   # Windows PowerShell
   source .venv/bin/activate    # macOS / Linux
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in the API keys:

   ```
   OPENROUTER_API_KEY=<your key>
   TAVILY_API_KEY=<your key>
   ```

   `OPENROUTER_BASE_URL` and `OPENROUTER_MODEL` have sensible defaults
   (`https://openrouter.ai/api/v1` and `google/gemma-4-31b-it`); set them
   only if you want to override.

## Running

```
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

## Example requests

### Without category (general top news)

```
curl -X POST http://127.0.0.1:8000/news \
  -H "Content-Type: application/json" \
  -d '{}'
```

### With category

```
curl -X POST http://127.0.0.1:8000/news \
  -H "Content-Type: application/json" \
  -d '{"category": "tech"}'
```

Allowed categories: `tech`, `economics`, `politics`. Omit the field for
general news.

### Example response

```json
{
  "summary": "Major technology companies are seeing mixed results from their investments in artificial intelligence, with Alphabet showing strong growth in its cloud and AI products. In the mobile world, Samsung is releasing security upgrades for the Galaxy S25 to better protect user data from theft. Meanwhile, experts are discussing a shift in how AI models are built, moving toward hybrid systems to improve efficiency.",
  "sources": [
    "https://www.bloomberg.com/news/articles/2026-05-03/big-tech-earnings-show-split-between-ai-trade-winners-and-losers",
    "https://www.forbes.com/sites/zakdoffman/2026/05/03/starting-with-galaxy-s25-samsungs-free-upgrade-goes-live/",
    "https://www.forbes.com/sites/johnwerner/2026/05/03/transformer-architecture-superpowers-and-the-march-toward-agi/"
  ]
}
```

## Validation behavior

- An invalid category returns **HTTP 422** with a clear validation message
  (handled automatically by FastAPI / Pydantic).
- Source URLs are validated as proper HTTP(S) links via Pydantic's `HttpUrl`.
- The response always contains a non-empty `summary` and between 1 and 5 sources.
- If the upstream agent fails (model error, search outage, schema violation),
  the endpoint returns **HTTP 502** with a short message — no stack traces leak.

## Smoke tests

Two scripts verify the wiring without going through the HTTP layer:

- `python scripts/smoke_test.py` — pings OpenRouter and Tavily with the
  configured keys to confirm credentials and connectivity.
- `python scripts/test_agent.py` — runs the agent end-to-end for both
  general news and the `tech` category, then validates the schema.

Both make real API calls (a fraction of a cent on OpenRouter, two free
Tavily searches per run).

## Design notes

**Why OpenRouter via `ChatOpenAI`** — OpenRouter exposes an OpenAI-compatible
API, so the standard `langchain-openai` integration works by overriding
`base_url`. No custom client, no extra adapter. Switching models is a
one-line config change.

**Why `days=2` is enforced at the Tavily layer** — the `langchain-tavily`
0.2.18 wrapper does not expose `days` as a constructor field, but the
underlying Tavily REST API supports it for the `news` topic and the wrapper
passes unknown kwargs through. A thin `_NewsTavilySearch` subclass injects
`days=2` on every call. Pushing the time-window constraint to the source
is cheaper and more reliable than fetching a wider set and post-filtering.

**Why structured output via `response_format=NewsResponse`** — the agent
returns a `NewsResponse` Pydantic instance directly. The constraints
(non-empty summary, 1-5 sources, valid HTTP URLs) are validated by
Pydantic before the model "decides" to stop, eliminating manual JSON
parsing and the bug class that comes with it.

**Why a factory pattern for the LLM and tool** — both `get_llm()` and
`get_news_search_tool()` build fresh instances on demand. This keeps each
caller free to construct its own client (relevant for tests and per-request
isolation) and makes mocking trivial (`monkeypatch` the factory).

## Notes on the take-home task

Built as the take-home for the AlphaCorp Junior AI Agent Engineer position.
