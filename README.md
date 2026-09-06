# Newspaper Delivery AI Agent

A FastAPI service that delivers a plain-language summary of the most
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

**Requires Python 3.12+.**

1. Clone the repo.
2. Create and activate a virtual environment:

   ```bash
   # macOS / Linux
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

   ```powershell
   # Windows PowerShell — use `py -3.12` if you have multiple Python
   # versions installed, to avoid `python` resolving to a different one.
   py -3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   > If activation fails with *"execution of scripts is disabled on this
   > system"*, allow signed local scripts once for your user with:
   > `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in the API keys:

   ```bash
   # macOS / Linux
   cp .env.example .env
   ```

   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

   ```
   OPENROUTER_API_KEY=<your key>
   TAVILY_API_KEY=<your key>
   ```

   `OPENROUTER_BASE_URL` and `OPENROUTER_MODEL` have sensible defaults
   (`https://openrouter.ai/api/v1` and `google/gemma-4-31b-it`); set them
   only if you want to override.

5. (Optional) Verify your keys before starting the server:

   ```bash
   python scripts/smoke_test.py
   ```

   This pings OpenRouter and Tavily directly and exits non-zero if either
   key is wrong — much faster than discovering the problem through a 502
   from the running API. See [Smoke tests](#smoke-tests) for details.

## Running

```bash
uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs

> **Expect each `/news` request to take ~30–60 seconds.** The endpoint
> waits for both the Tavily search and the LLM summarization to finish
> before responding; this is the agent working, not a hang.

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

## Limitations

Two of these are genuine soft spots; the rest are scope.

- **Summary faithfulness is unverified.** Pydantic guarantees the *shape* of
  the response — non-empty summary, 1-5 valid URLs — but nothing checks that
  the summary reflects the articles behind those URLs. Misattribution would
  pass through silently. This is the obvious next piece of work, and it needs
  an eval harness rather than another assertion.
- **The `days=2` filter rests on kwarg passthrough.** `langchain-tavily`
  0.2.18 forwards unknown kwargs verbatim, which is what makes the injection
  work at all. A future version that validates kwargs would drop the time
  window *silently* rather than raising — so the pin in `requirements.txt` is
  load-bearing, not cosmetic.
- **Verification is by smoke script, not by suite.** The scripts under
  `scripts/` call the real OpenRouter and Tavily APIs, which is the point:
  they catch credential and contract breakage that a mocked test cannot. The
  cost is that they spend quota and cannot gate CI.
- **Single-process and stateless by design.** No cache, no job queue, no
  persistence — each request runs the full search-and-summarise cycle and
  holds the connection for its 30-60 seconds. Adding a queue would change the
  API contract, which is out of scope for a synchronous briefing endpoint.
- **The service assumes a trusted caller.** The endpoint is unauthenticated
  and unthrottled, so it is meant to run behind something that isn't.
- **Categories are a closed set** — `tech`, `economics`, `politics`, or
  general. Anything else is a 422, which is the intended behaviour rather
  than a gap.

## About

A study project on agent design and structured output: what it takes for an
LLM-backed endpoint to return a validated object instead of a blob of text,
and where the boundary belongs between what the model decides and what the
code enforces.
