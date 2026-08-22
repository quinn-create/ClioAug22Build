from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    clio_api_version: str = Field(default="4.0.0")

    provider: Literal["clio", "mycase"] = "clio"

    mcp_transport: Literal["stdio", "http", "streamable-http"] = "stdio"
    mcp_http_api_key: str = ""

    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "INFO"

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
