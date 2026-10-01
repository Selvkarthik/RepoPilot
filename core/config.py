import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Centralized application configuration loaded from environment variables."""

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    # LLM / OpenRouter
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "inclusionai/ling-3.0-flash-fin:free"

    # PostgreSQL / pgvector
    DB_URL: str = ""

    # Redis & Celery
    REDIS_BROKER_URL: str = "redis://localhost:6379/0"
    REDIS_RESULT_BACKEND: str = "redis://localhost:6379/1"
    REDIS_CACHE_URL: str = "redis://localhost:6379/2"

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        return cls(
            GITHUB_TOKEN=os.getenv("GITHUB_TOKEN", ""),
            GITHUB_WEBHOOK_SECRET=os.getenv("GITHUB_WEBHOOK_SECRET", ""),
            OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY", ""),
            OPENROUTER_MODEL=os.getenv(
                "OPENROUTER_MODEL", "inclusionai/ling-3.0-flash-fin:free"
            ),
            DB_URL=os.getenv("DB_URL", ""),
            REDIS_BROKER_URL=os.getenv(
                "REDIS_BROKER_URL", "redis://localhost:6379/0"
            ),
            REDIS_RESULT_BACKEND=os.getenv(
                "REDIS_RESULT_BACKEND", "redis://localhost:6379/1"
            ),
            REDIS_CACHE_URL=os.getenv(
                "REDIS_CACHE_URL", "redis://localhost:6379/2"
            ),
        )


settings = Settings.load()
