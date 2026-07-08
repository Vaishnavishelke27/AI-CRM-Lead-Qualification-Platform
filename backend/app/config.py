import os


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ai_crm",
    )
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    claude_api_key: str | None = os.getenv("CLAUDE_API_KEY")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
    ai_cache_ttl_seconds: int = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))
    ai_rate_limit_per_minute: int = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "30"))
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    reporting_interval_minutes: int = int(os.getenv("REPORTING_INTERVAL_MINUTES", "1440"))
    reporting_email_to: str | None = os.getenv("REPORTING_EMAIL_TO")
    frontend_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    public_api_base_url: str = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")


settings = Settings()
