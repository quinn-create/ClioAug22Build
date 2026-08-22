from __future__ import annotations

import httpx
import pytest

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.client import ClioClient


@pytest.fixture
def settings() -> Settings:
    return Settings(
        clio_client_id="id",
        clio_client_secret="secret",
        clio_refresh_token="refresh",
        clio_base_url="https://app.clio.com",
        mcp_transport="http",
        mcp_http_api_key="test-key",
    )


@pytest.fixture
def client(settings: Settings) -> ClioClient:
    http = httpx.AsyncClient(timeout=5.0)
    return ClioClient(settings, http=http)
