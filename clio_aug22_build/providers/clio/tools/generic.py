from __future__ import annotations

from typing import Any, Literal, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_api_request")
    async def clio_api_request(
        method: Literal["GET", "POST", "PATCH", "PUT", "DELETE"],
        path: str,
        query: Optional[dict[str, Any]] = None,
        body: Optional[Any] = None,
        raw: bool = False,
        auto_page: bool = False,
        max_pages: int = 5,
    ) -> dict[str, Any]:
        """Generic Clio Manage API v4 fallback. Use ONLY when no specialized clio_* tool exists.

        path: '/custom_fields', '/matters/123', or a full https URL on the configured Clio host.
        Off-host URLs are rejected (SSRF protection).

        Envelope (POST/PATCH/PUT):
        - raw=false (DEFAULT): wrap body in Clio's required {"data": {...}}.
          If body already has a top-level "data" key, it is NOT double-wrapped.
        - raw=true: send body exactly as given. Use this to bypass wrapping.

        If fields is omitted on GET, known resources get a default field set so you do not
        only receive id/etag. Prefer specialized tools for contacts, matters, calendar,
        tasks, activities, notes, and documents.
        """
        return await provider.raw_request(
            method=method,
            path=path,
            query=query,
            body=body,
            raw=raw,
            auto_page=auto_page,
            max_pages=max_pages,
        )
