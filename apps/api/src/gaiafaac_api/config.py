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

    # Customer self-service. Empty integration values keep delivery securely disabled.
    customer_app_url: str = "http://localhost:3000"
    customer_alert_email_enabled: bool = False
    institutional_webhook_enabled: bool = False
    institutional_webhook_master_secret: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_analyst: str = ""
    stripe_price_team: str = ""
    stripe_price_api: str = ""

    # Payment processing (Paystack). Empty values keep billing features disabled.
    paystack_public_key: str = ""
    paystack_secret_key: str = ""
    paystack_webhook_secret: str = ""
    paystack_sandbox_mode: bool = False

    # Invoice delivery (Zoho Mail).
    zoho_sender_email: str = ""
    zoho_sender_password: str = ""

    # Durable retention for collected source documents (S3-compatible object storage).
    # Empty values keep archive pipelines failing closed rather than writing to an
    # ephemeral local/CI filesystem the deployed service can never read back.
    source_archive_bucket: str = ""
    source_archive_endpoint: str = ""
    source_archive_access_key_id: str = ""
    source_archive_secret_access_key: str = ""
    source_archive_region: str = "auto"

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
        "institutional_webhook_master_secret",
        "stripe_secret_key",
        "stripe_webhook_secret",
        "stripe_price_analyst",
        "stripe_price_team",
        "stripe_price_api",
        "paystack_public_key",
        "paystack_secret_key",
        "paystack_webhook_secret",
        "zoho_sender_email",
        "zoho_sender_password",
        "source_archive_bucket",
        "source_archive_endpoint",
        "source_archive_access_key_id",
        "source_archive_secret_access_key",
        "source_archive_region",
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
