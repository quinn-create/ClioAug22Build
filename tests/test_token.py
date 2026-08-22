from __future__ import annotations

import httpx
import pytest
import respx

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.token import TokenError, TokenManager


def _settings() -> Settings:
    return Settings(
        clio_client_id="id",
        clio_client_secret="secret",
        clio_refresh_token="refresh",
        clio_base_url="https://app.clio.com",
    )


@pytest.mark.asyncio
async def test_refresh_and_cache() -> None:
    settings = _settings()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert b"grant_type=refresh_token" in request.content
        assert b"refresh_token=refresh" in request.content
        return httpx.Response(
            200,
            json={"access_token": "tok-1", "expires_in": 2592000, "token_type": "bearer"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        mgr = TokenManager(settings, http)
        a = await mgr.get_access_token()
        b = await mgr.get_access_token()
        assert a == b == "tok-1"
        assert calls["n"] == 1


@pytest.mark.asyncio
async def test_force_refresh() -> None:
    settings = _settings()
    n = {"i": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        n["i"] += 1
        return httpx.Response(200, json={"access_token": f"tok-{n['i']}", "expires_in": 2592000})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        mgr = TokenManager(settings, http)
        assert await mgr.get_access_token() == "tok-1"
        assert await mgr.get_access_token(force=True) == "tok-2"


@pytest.mark.asyncio
async def test_bad_credentials() -> None:
    settings = _settings()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "invalid_grant"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        mgr = TokenManager(settings, http)
        with pytest.raises(TokenError):
            await mgr.get_access_token()


@pytest.mark.asyncio
async def test_missing_env() -> None:
    settings = Settings()
    async with httpx.AsyncClient() as http:
        mgr = TokenManager(settings, http)
        with pytest.raises(TokenError):
            await mgr.get_access_token()


@pytest.mark.asyncio
@respx.mock
async def test_respx_endpoint() -> None:
    settings = _settings()
    respx.post("https://app.clio.com/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "abc", "expires_in": 100})
    )
    async with httpx.AsyncClient() as http:
        mgr = TokenManager(settings, http)
        assert await mgr.get_access_token() == "abc"
