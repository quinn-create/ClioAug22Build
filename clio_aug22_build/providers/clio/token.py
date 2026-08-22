from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.constants import USER_AGENT

logger = logging.getLogger(__name__)


class TokenError(RuntimeError):
    def __init__(self, message: str, status: int = 401) -> None:
        super().__init__(message)
        self.status = status


class TokenManager:
    """In-memory access-token cache. Refresh token stays in env and is not rotated."""

    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._http = http
        self._lock = asyncio.Lock()
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    @property
    def has_token(self) -> bool:
        return bool(self._access_token)

    async def get_access_token(self, *, force: bool = False) -> str:
        if not self._settings.has_clio_credentials:
            raise TokenError(
                "Missing CLIO_CLIENT_ID, CLIO_CLIENT_SECRET, or CLIO_REFRESH_TOKEN",
                status=503,
            )
        async with self._lock:
            now = time.time()
            if (
                not force
                and self._access_token
                and now < self._expires_at - 300
            ):
                return self._access_token
            await self._refresh()
            assert self._access_token is not None
            return self._access_token

    async def probe(self) -> dict[str, Any]:
        try:
            await self.get_access_token()
            return {"ok": True, "clio_auth": "ok"}
        except TokenError as exc:
            return {"ok": False, "clio_auth": "error", "message": str(exc)}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Clio auth probe failed: %s", type(exc).__name__)
            return {
                "ok": False,
                "clio_auth": "error",
                "message": "Clio token refresh failed",
            }

    async def _refresh(self) -> None:
        logger.info("Refreshing Clio access token")
        try:
            response = await self._http.post(
                self._settings.clio_token_url,
                data={
                    "client_id": self._settings.clio_client_id,
                    "client_secret": self._settings.clio_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self._settings.clio_refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": USER_AGENT,
                },
            )
        except httpx.HTTPError as exc:
            raise TokenError(f"Token endpoint unreachable: {type(exc).__name__}", status=503) from exc

        if response.status_code >= 400:
            raise TokenError(
                "Clio rejected the token. Re-check Client ID / Secret / Refresh Token.",
                status=response.status_code,
            )
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise TokenError("Clio token response missing access_token")
        self._access_token = token
        expires_in = int(payload.get("expires_in") or 2592000)
        self._expires_at = time.time() + expires_in
        logger.info("Clio access token refreshed, expires_in=%s", expires_in)
