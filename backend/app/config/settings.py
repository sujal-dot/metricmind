from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)

_PLACEHOLDER_SECRETS = {
    "",
    "change-me-in-prod",
    "change-me-to-a-random-secret-in-production",
    "metricmind-secret-change-me",
    "your-secret-key",
    "your-secret-here",
}


class Settings(BaseSettings):
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    docs_enabled: bool | None = None

    database_url: str = "sqlite:///./dev.db"
    db_pool_size: int = Field(default=20, ge=1, le=100)
    db_max_overflow: int = Field(default=40, ge=0, le=200)
    db_pool_recycle: int = Field(default=1800, ge=60)
    db_pool_pre_ping: bool = True

    openai_api_key: str = ""
    groq_api_key: str = ""
    gemini_api_key: str = ""
    cube_api_url: str = "http://localhost:4000/cubejs-api/v1"
    cube_api_token: str = ""
    cube_api_secret: str = "change-me-in-prod"
    llm_provider: Literal["groq", "openai", "gemini"] = "groq"
    groq_model: str = "llama-3.3-70b-versatile"
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-1.5-pro"

    jwt_secret_key: str = "change-me-to-a-random-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = Field(default=60 * 24, ge=5)

    session_cookie_name: str = "metricmind_session"
    session_cookie_secure: bool | None = None
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_ttl_minutes: int = Field(default=60 * 12, ge=5)
    csrf_cookie_name: str = "metricmind_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    rate_limit_per_minute: int = Field(default=30, ge=1)
    rate_limit_ask_per_minute: int = Field(default=10, ge=1)

    run_migrations_on_startup: bool = False
    seed_on_boot: bool = False

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def effective_docs_enabled(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return not self.is_production

    @property
    def effective_session_cookie_secure(self) -> bool:
        if self.session_cookie_secure is not None:
            return self.session_cookie_secure
        return self.is_production

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if not self.is_production:
            return self

        errors: list[str] = []
        if self.debug:
            errors.append("DEBUG must be false in production")
        if not self.allowed_origins or "*" in self.allowed_origins:
            errors.append("ALLOWED_ORIGINS must be an explicit allowlist in production")
        if self.session_cookie_samesite == "none" and not self.effective_session_cookie_secure:
            errors.append("SameSite=None session cookies require Secure=true")
        if self.jwt_secret_key in _PLACEHOLDER_SECRETS or len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY must be a strong non-placeholder secret in production")
        if self.cube_api_secret in _PLACEHOLDER_SECRETS:
            errors.append("CUBE_API_SECRET must be configured in production")

        db = urlparse(self.database_url)
        if db.username == "metricmind" and db.password == "metricmind":
            errors.append("DATABASE_URL must not use default metricmind:metricmind credentials in production")

        if errors:
            raise ValueError("Production configuration is unsafe: " + "; ".join(errors))
        return self

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False


settings = Settings()
