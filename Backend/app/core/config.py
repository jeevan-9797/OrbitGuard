"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """OrbitGuard backend configuration.

    Values are read from environment variables (or a `.env` file located at the
    project root).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Server ───────────────────────────────────────────────────────────
    APP_NAME: str = "OrbitGuard API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    PORT: int = 8001

    # ── Supabase ─────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ── LLM / AI Provider ───────────────────────────────────────────────
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_ENDPOINT: str = ""

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
