from __future__ import annotations

from typing import ClassVar

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///data/leadgen.db")
    app_name: str = Field(default="LeadGen Agent")
    log_level: str = Field(default="INFO")
    browser_ws_url: str = Field(default="ws://127.0.0.1:10086/ws")
    browser_timeout: float = Field(default=30.0)
    openai_api_key: str | None = Field(default=None)
    stripe_api_key: str | None = Field(default=None)
    stripe_price_id: str = Field(default="price_99_month")
    stripe_webhook_secret: str | None = Field(default=None)
    sendgrid_api_key: str | None = Field(default=None)
    from_email: str = Field(default="noreply@leadgen.app")
    from_name: str = Field(default="LeadGen Agent")
    sentry_dsn: str | None = Field(default=None)
    api_key: str | None = Field(default=None)

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _fail_fast_in_production(self) -> Settings:
        """Raise ``RuntimeError`` if required env vars are missing in production.

        "Production" is heuristically detected as any non-SQLite database URL
        (PostgreSQL, etc.).  SQLite is assumed local/dev.
        """
        if self.database_url and not self.database_url.startswith("sqlite"):
            missing: list[str] = []
            if not self.stripe_api_key:
                missing.append("STRIPE_API_KEY")
            if not self.sendgrid_api_key:
                missing.append("SENDGRID_API_KEY")
            if missing:
                raise RuntimeError(
                    "FATAL: Missing required environment variables for production:\n"
                    "  " + "\n  ".join(missing) + "\n"
                    "These must be set before the application can start.\n"
                    "See .env.example for configuration instructions."
                )
        return self


settings = Settings()
