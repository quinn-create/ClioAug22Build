from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _running_on_railway() -> bool:
    return any(
        os.getenv(name)
        for name in (
            "RAILWAY_ENVIRONMENT",
            "RAILWAY_ENVIRONMENT_ID",
            "RAILWAY_PROJECT_ID",
            "RAILWAY_SERVICE_ID",
        )
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    clio_client_id: str = ""
    clio_client_secret: str = ""
    clio_refresh_token: str = ""
    clio_base_url: str = Field(default="https://app.clio.com")
    clio_api_version: str = Field(default="")

    provider: Literal["clio", "mycase"] = "clio"

    mcp_transport: Literal["stdio", "http", "streamable-http"] = "stdio"
    mcp_http_api_key: str = ""

    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

    @field_validator("mcp_transport", mode="before")
    @classmethod
    def _normalize_transport(cls, value: object) -> object:
        if value is None:
            return "stdio"
        text = str(value).strip().lower()
        if text in ("", "stdio"):
            return "stdio"
        if text in ("http", "streamable-http", "streamable_http", "sse"):
            return "http" if text != "streamable-http" else "streamable-http"
        return value

    @model_validator(mode="after")
    def _http_on_railway(self) -> "Settings":
        # Railway health checks need /health. Never start stdio in the cloud.
        if _running_on_railway():
            self.mcp_transport = "http"
            self.host = "0.0.0.0"
        return self

    @property
    def clio_root(self) -> str:
        return self.clio_base_url.rstrip("/")

    @property
    def clio_api_root(self) -> str:
        return f"{self.clio_root}/api/v4"

    @property
    def clio_token_url(self) -> str:
        return f"{self.clio_root}/oauth/token"

    @property
    def has_clio_credentials(self) -> bool:
        return bool(
            self.clio_client_id and self.clio_client_secret and self.clio_refresh_token
        )

    @property
    def is_http(self) -> bool:
        return self.mcp_transport in ("http", "streamable-http")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
