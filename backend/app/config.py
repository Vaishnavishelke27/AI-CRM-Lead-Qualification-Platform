import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def load_environment(env_file: Path = ROOT_ENV_FILE) -> None:
    load_dotenv(env_file, override=False)


load_environment()


def required_secret(name: str, minimum_length: int = 32) -> str:
    value = os.getenv(name, "")
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} must be set and contain at least {minimum_length} characters")
    return value


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./local_ai_crm.db",
    )
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    claude_api_key: str | None = os.getenv("CLAUDE_API_KEY")
    ai_provider: str = os.getenv("AI_PROVIDER", "openai")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-haiku-latest")
    ai_cache_ttl_seconds: int = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))
    ai_rate_limit_per_minute: int = int(os.getenv("AI_RATE_LIMIT_PER_MINUTE", "30"))
    jwt_secret_key: str = required_secret("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    crm_webhook_secret: str | None = os.getenv("CRM_WEBHOOK_SECRET") or None
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    reporting_interval_minutes: int = int(os.getenv("REPORTING_INTERVAL_MINUTES", "1440"))
    reporting_email_to: str | None = os.getenv("REPORTING_EMAIL_TO")
    smtp_host: str | None = os.getenv("SMTP_HOST") or None
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str | None = os.getenv("SMTP_USERNAME") or None
    smtp_password: str | None = os.getenv("SMTP_PASSWORD") or None
    smtp_from_email: str | None = os.getenv("SMTP_FROM_EMAIL") or None
    smtp_starttls: bool = os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes", "on"}
    frontend_origins: list[str] = [
        origin.strip()
        for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if origin.strip()
    ]
    public_api_base_url: str = os.getenv("PUBLIC_API_BASE_URL", "http://localhost:8000")
    email_click_allowed_hosts: set[str] = {
        host.strip().lower()
        for host in os.getenv("EMAIL_CLICK_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    }


settings = Settings()
