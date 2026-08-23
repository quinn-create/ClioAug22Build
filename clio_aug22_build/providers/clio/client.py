from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.constants import PATH_RESOURCE_FIELDS, USER_AGENT
from clio_aug22_build.providers.clio.token import TokenError, TokenManager
from clio_aug22_build.providers.clio.util import (
    WRITE_METHODS,
    PathSafetyError,
    drop_none,
    fail,
    normalize_clio_path,
    ok,
    paging_from_payload,
    resource_from_path,
    wrap_body,
)

logger = logging.getLogger(__name__)


class ClioApiError(RuntimeError):
    def __init__(self, status: int, error: str, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.error = error
        self.hint = hint

    def as_dict(self) -> dict[str, Any]:
        return fail(self.status, self.error, str(self), self.hint)


class ClioClient:
    def __init__(self, settings: Settings, http: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.http = http or httpx.AsyncClient(timeout=30.0)
        self.tokens = TokenManager(settings, self.http)

    async def close(self) -> None:
        await self.http.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        body: Any = None,
        raw: bool = False,
        default_fields: str | None = None,
        auto_page: bool = False,
        max_pages: int = 5,
    ) -> dict[str, Any]:
        method = method.upper()
        try:
            url, extra_query = normalize_clio_path(path, self.settings.clio_api_root)
        except PathSafetyError as exc:
            return fail(400, "path_safety", str(exc), "Use a /api/v4 relative path on the configured Clio host")

        params = drop_none(query)
        for key, value in extra_query.items():
            params.setdefault(key, value)

        injected = False
        if method == "GET" and not params.get("fields"):
            resource = resource_from_path(urlparse_path(url))
            fields = default_fields or PATH_RESOURCE_FIELDS.get(resource)
            if fields:
                params["fields"] = fields
                injected = True

        json_body = wrap_body(body, raw=raw) if method in WRITE_METHODS else None

        pages: list[Any] = []
        last_payload: Any = None
        pages_fetched = 0
        next_url: str | None = url
        next_params: dict[str, Any] | None = params

        while next_url:
            payload = await self._send(method, next_url, params=next_params, json_body=json_body)
            last_payload = payload
            pages_fetched += 1
            data = payload.get("data") if isinstance(payload, dict) else payload
            if auto_page and isinstance(data, list):
                pages.extend(data)
                paging = (payload.get("meta") or {}).get("paging") or {}
                nxt = paging.get("next")
                if nxt and pages_fetched < max_pages:
                    next_url, extra = normalize_clio_path(nxt, self.settings.clio_api_root)
                    next_params = extra or None
                    json_body = None
                    continue
            break

        if auto_page and pages:
            paging = paging_from_payload(last_payload) if pages_fetched >= max_pages else {
                "has_next": False,
                "next_page_token": None,
            }
            warning = "fields was omitted; default fields were injected" if injected else None
            if pages_fetched >= max_pages and paging_from_payload(last_payload)["has_next"]:
                warning = ((warning + " | ") if warning else "") + (
                    f"Stopped after max_pages={max_pages}; pass page_token to continue"
                )
            return ok(pages, paging=paging, warning=warning)

        data = last_payload.get("data") if isinstance(last_payload, dict) else last_payload
        warning = None
        if injected:
            warning = "fields was omitted; default fields were injected so you did not only get id/etag"
        return ok(data, paging=paging_from_payload(last_payload), warning=warning)

    async def _send(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None,
        json_body: Any,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        unauthorized_retried = False
        for attempt in range(4):
            try:
                token = await self.tokens.get_access_token(force=unauthorized_retried and attempt > 0)
            except TokenError as exc:
                raise ClioApiError(exc.status, "auth_error", str(exc)) from exc

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            }
            if self.settings.clio_api_version:
                headers["X-API-VERSION"] = self.settings.clio_api_version
            if json_body is not None:
                headers["Content-Type"] = "application/json"

            try:
                response = await self.http.request(
                    method,
                    url,
                    params=params if params else None,
                    json=json_body,
                    headers=headers,
                )
            except httpx.HTTPError as exc:
                last_error = exc
                await asyncio.sleep(min(2 ** attempt, 8))
                continue

            remaining = response.headers.get("X-RateLimit-Remaining")
            logger.info(
                "Clio %s %s -> %s remaining=%s",
                method,
                _safe_path(url),
                response.status_code,
                remaining,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
                await asyncio.sleep(min(delay, 30))
                continue

            if response.status_code == 401 and not unauthorized_retried:
                unauthorized_retried = True
                await self.tokens.get_access_token(force=True)
                continue

            if response.status_code >= 400:
                raise _api_error_from_response(response)

            if not response.content:
                return {"data": None}
            try:
                payload = response.json()
            except ValueError as exc:
                raise ClioApiError(502, "invalid_json", "Clio returned a non-JSON body") from exc
            if not isinstance(payload, dict):
                return {"data": payload}
            return payload

        raise ClioApiError(
            503,
            "upstream_error",
            f"Clio request failed after retries ({type(last_error).__name__ if last_error else 'unknown'})",
        )


def urlparse_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path


def _safe_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path


def _api_error_from_response(response: httpx.Response) -> ClioApiError:
    message = response.text[:500]
    error_name = "clio_error"
    hint = None
    try:
        payload = response.json()
        if isinstance(payload, dict):
            err = payload.get("error") or payload
            if isinstance(err, dict):
                error_name = str(err.get("type") or err.get("class") or "clio_error")
                message = str(err.get("message") or err.get("description") or message)
            elif isinstance(err, str):
                error_name = err
                message = str(payload.get("error_description") or message)
    except ValueError:
        pass
    if response.status_code == 403:
        hint = "This record may be billed, locked, or outside your Clio permission set."
    if response.status_code == 422:
        hint = "Check required nested IDs ({id: N}), the data envelope, and field types."
    if response.status_code == 400 and "fields" in message.lower():
        hint = "Nested fields can only go one level deep: matter{id,description} is ok; matter{client{name}} is not."
    return ClioApiError(response.status_code, error_name, message, hint)
