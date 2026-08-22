from __future__ import annotations

import httpx
import pytest
import respx

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.client import ClioClient


def _settings() -> Settings:
    return Settings(
        clio_client_id="id",
        clio_client_secret="secret",
        clio_refresh_token="refresh",
        clio_base_url="https://app.clio.com",
    )


@pytest.mark.asyncio
@respx.mock
async def test_auto_wraps_post_body() -> None:
    settings = _settings()
    respx.post("https://app.clio.com/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 2592000})
    )

    def capture(request: httpx.Request) -> httpx.Response:
        assert request.content == b'{"data":{"first_name":"Jane","type":"Person"}}'
        return httpx.Response(201, json={"data": {"id": 1, "first_name": "Jane"}})

    respx.post("https://app.clio.com/api/v4/contacts").mock(side_effect=capture)
    async with httpx.AsyncClient() as http:
        client = ClioClient(settings, http=http)
        result = await client.request(
            "POST",
            "/contacts",
            body={"first_name": "Jane", "type": "Person"},
            query={"fields": "id,first_name"},
        )
        assert result["ok"] is True
        assert result["data"]["id"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_raw_true_skips_wrap() -> None:
    settings = _settings()
    respx.post("https://app.clio.com/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 2592000})
    )

    def capture(request: httpx.Request) -> httpx.Response:
        assert request.content == b'{"first_name":"Jane"}'
        return httpx.Response(400, json={"error": {"type": "ArgumentError", "message": "data required"}})

    respx.post("https://app.clio.com/api/v4/contacts").mock(side_effect=capture)
    async with httpx.AsyncClient() as http:
        client = ClioClient(settings, http=http)
        with pytest.raises(Exception) as exc:
            await client.request("POST", "/contacts", body={"first_name": "Jane"}, raw=True)
        assert "data required" in str(exc.value) or getattr(exc.value, "status", None) == 400


@pytest.mark.asyncio
@respx.mock
async def test_401_retries_once() -> None:
    settings = _settings()
    token_calls = {"n": 0}

    def token(_request: httpx.Request) -> httpx.Response:
        token_calls["n"] += 1
        return httpx.Response(
            200, json={"access_token": f"tok-{token_calls['n']}", "expires_in": 2592000}
        )

    respx.post("https://app.clio.com/oauth/token").mock(side_effect=token)
    route = respx.get("https://app.clio.com/api/v4/users/who_am_i").mock(
        side_effect=[
            httpx.Response(401, json={"error": "unauthorized"}),
            httpx.Response(200, json={"data": {"id": 7, "name": "Quinn"}}),
        ]
    )
    async with httpx.AsyncClient() as http:
        client = ClioClient(settings, http=http)
        result = await client.request("GET", "/users/who_am_i", query={"fields": "id,name"})
        assert result["ok"] is True
        assert result["data"]["id"] == 7
        assert route.call_count == 2
        assert token_calls["n"] >= 2


@pytest.mark.asyncio
@respx.mock
async def test_injects_default_fields() -> None:
    settings = _settings()
    respx.post("https://app.clio.com/oauth/token").mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 2592000})
    )

    def capture(request: httpx.Request) -> httpx.Response:
        assert b"fields=" in request.url.query
        return httpx.Response(200, json={"data": [{"id": 1}], "meta": {}})

    respx.get("https://app.clio.com/api/v4/contacts").mock(side_effect=capture)
    async with httpx.AsyncClient() as http:
        client = ClioClient(settings, http=http)
        result = await client.request("GET", "/contacts")
        assert result["ok"] is True
        assert "default fields were injected" in (result.get("warning") or "")
