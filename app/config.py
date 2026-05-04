"""Application settings loaded from environment / .env file.

A single `Settings` instance is exposed via `get_settings()`, cached with
`functools.lru_cache`. The lru_cache pattern (rather than a bare module-level
instance) is deliberate:

  * env vars are read lazily on first access — friendlier to tests that
    set vars before the first call;
  * it plugs straight into FastAPI's `Depends(get_settings)` and can be
    overridden via `app.dependency_overrides` in tests.

For convenience, `settings` is also exposed as a module-level alias for
scripts and non-FastAPI callers that just want `from app.config import settings`.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    OPENROUTER_API_KEY: str = Field(..., min_length=1)
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it"

    TAVILY_API_KEY: str = Field(..., min_length=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
