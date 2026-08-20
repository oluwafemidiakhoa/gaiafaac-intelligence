from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _normalize_database_url(url: str) -> str:
    """Force the psycopg3 driver for bare Postgres URLs."""
    for bare in ("postgresql://", "postgres://"):
        if url.startswith(bare):
            return "postgresql+psycopg://" + url[len(bare) :]
    return url


class Settings(BaseSettings):
    """Validated runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )

    api_environment: str = Field(default="development")
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = Field(
        default="postgresql+psycopg://gaiafaac:change-me@localhost:5432/gaiafaac",
    )
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    alert_from: str = ""
    alert_to: str = ""
    admin_key: str = ""

    # Customer self-service. Empty Stripe values keep billing securely disabled.
    customer_app_url: str = "http://localhost:3000"
    customer_alert_email_enabled: bool = False
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_analyst: str = ""
    stripe_price_team: str = ""
    stripe_price_api: str = ""

    @field_validator(
        "api_environment",
        "api_host",
        "database_url",
        "smtp_port",
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "alert_from",
        "alert_to",
        "admin_key",
        "customer_app_url",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "stripe_price_analyst",
        "stripe_price_team",
        "stripe_price_api",
        mode="before",
    )
    @classmethod
    def _clean_or_default(cls, value: object, info: ValidationInfo) -> object:
        if isinstance(value, str):
            if info.field_name == "database_url":
                cleaned = _normalize_database_url("".join(value.split()))
            else:
                cleaned = value.strip()
            if not cleaned:
                return cls.model_fields[info.field_name].default
            return cleaned
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
