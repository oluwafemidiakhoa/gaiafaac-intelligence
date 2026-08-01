from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    # Shared admin key gating operational/review endpoints. Empty = deny all (secure default).
    admin_key: str = ""

    @field_validator("api_environment", "api_host", "database_url", mode="before")
    @classmethod
    def _default_when_blank(cls, value: object, info: ValidationInfo) -> object:
        """Treat a blank env var as unset so it cannot crash startup.

        Deployment platforms (e.g. Railway) frequently ship variables set to an
        empty string. Without this, an empty ``API_ENVIRONMENT`` would override
        the default and raise a validation error before the app can even serve
        its health check. Fall back to the field default instead.
        """
        if isinstance(value, str) and not value.strip():
            return cls.model_fields[info.field_name].default
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
