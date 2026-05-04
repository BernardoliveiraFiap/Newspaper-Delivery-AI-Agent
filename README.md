# Newspaper Delivery AI Agent

FastAPI service that exposes a LangChain agent which fetches recent news
via Tavily Search and returns a plain-language summary plus source links.

## Stack

- **Python 3.11+**
- **FastAPI** + **Uvicorn** — HTTP layer
- **Pydantic v2** + **pydantic-settings** — schemas & config
- **LangChain** — agent orchestration
- **OpenRouter** (via `langchain-openai`, OpenAI-compatible API) — LLM provider, model `google/gemma-4-31b-it`
- **Tavily Search** (via `langchain-tavily`) — web search tool

## Setup

```bash
git clone <repo-url>
cd Newspaper-Delivery-AI-Agent

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env                # Windows: copy .env.example .env
# then edit .env and fill in OPENROUTER_API_KEY and TAVILY_API_KEY
```

## Running

```bash
uvicorn app.main:app --reload
```

> TODO: `app/main.py` is currently empty (scaffolded only). The endpoint
> will be wired in the next milestone.

## Project structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py         # FastAPI app + routes (TODO)
│   ├── schemas.py      # request/response models (TODO)
│   ├── agent.py        # LangChain agent assembly (TODO)
│   ├── tools.py        # Tavily search tool config (TODO)
│   ├── llm.py          # OpenRouter ChatOpenAI factory (TODO)
│   └── config.py       # pydantic-settings Settings + get_settings()
├── .env.example        # template for required env vars
├── .gitignore
├── requirements.txt
├── pyproject.toml      # project metadata + ruff/pytest config
└── README.md
```

## API

To be documented at `/docs` (Swagger UI) once `app/main.py` is implemented.
