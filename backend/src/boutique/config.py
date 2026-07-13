from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_JWT_SECRET = "local-development-only-change-me"
_NON_PRODUCTION_ENVIRONMENTS = frozenset({"local", "test", "testing", "integration"})


class Settings(BaseSettings):
    app_name: str = "Boutique API"
    environment: str = "local"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://boutique:boutique@localhost:5433/boutique"
    redis_url: str = "redis://localhost:6380/0"
    dashboard_cache_ttl_seconds: int = 300
    serverless: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    auth0_domain: str | None = None
    auth0_audience: str | None = None
    jwt_secret: str = _LOCAL_JWT_SECRET
    jwt_access_ttl_minutes: int = 60
    jwt_refresh_ttl_days: int = 7
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    posthog_api_key: str | None = None
    posthog_host: str = "https://eu.i.posthog.com"
    sentry_dsn: str | None = None
    kaggle_username: str | None = None
    kaggle_key: str | None = None
    kaggle_olist_dataset: str = "olistbr/brazilian-ecommerce"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def require_secure_production_authentication(self) -> "Settings":
        if self.environment.lower() in _NON_PRODUCTION_ENVIRONMENTS:
            return self
        if self.jwt_secret == _LOCAL_JWT_SECRET or len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be a unique value of at least 32 characters")
        if not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true outside local and test environments")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("COOKIE_SAMESITE=none requires COOKIE_SECURE=true")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
