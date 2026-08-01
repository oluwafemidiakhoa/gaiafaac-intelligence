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

    @field_validator("api_environment", "api_host", "database_url", "smtp_port", mode="before")
    @classmethod
    def _clean_or_default(cls, value: object, info: ValidationInfo) -> object:
        """Strip surrounding whitespace and treat a blank env var as unset.

        Two failure modes this guards against:

        * Deployment platforms (e.g. Railway) frequently ship variables set to an
          empty string. Without this, an empty ``API_ENVIRONMENT`` would override
          the default and raise a validation error before the app can even serve
          its health check.
        * Secrets pasted into CI/CD often carry a trailing newline or space. A
          ``DATABASE_URL`` ending in ``sslmode=require\\n`` makes libpq reject the
          connection with "invalid sslmode value". Stripping makes it robust.

        Fall back to the field default when the value is blank.
        """
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return cls.model_fields[info.field_name].default
            return stripped
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
