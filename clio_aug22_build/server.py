from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response

from clio_aug22_build import __version__
from clio_aug22_build.config import Settings, get_settings
from clio_aug22_build.dashboard import TOOL_CATALOG, render_dashboard, render_oauth_page
from clio_aug22_build.logging_setup import setup_logging
from clio_aug22_build.providers.registry import build_provider
from clio_aug22_build.providers.clio.tools import register_clio_tools

logger = logging.getLogger(__name__)

INSTRUCTIONS = """
You are connected to ClioAug22Build, a Clio Manage MCP server for a single law-firm user.

RULES:
1. Always search/find/list before creating. Never create a duplicate contact, matter, task, calendar entry, time entry, or note.
2. Prefer specialized clio_* tools over clio_api_request.
3. Use clio_api_request only for endpoints that have no specialized tool.
4. clio_api_request auto-wraps POST/PATCH/PUT bodies in Clio's {"data": {...}} envelope unless raw=true.
5. Specialized time tools accept hours; Clio stores seconds internally (1.5 hours = 5400 seconds).
6. Flat fees: set custom_rate to the dollar amount (typically hours=1), or flat_rate=true with price.
7. Nested associations use {id: N}. Specialized tools accept a plain *_id integer and nest it for you.
8. If a GET looks empty, you forgot fields= — specialized tools already send a default field set.
""".strip()

OPEN_PATHS = {"/", "/health", "/ready", "/favicon.ico", "/oauth"}


class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        path = request.url.path
        if path in OPEN_PATHS or path.startswith("/health"):
            return await call_next(request)
        if not self.api_key:
            return await call_next(request)
        auth = request.headers.get("authorization") or ""
        if auth != f"Bearer {self.api_key}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def create_mcp(settings: Settings | None = None) -> tuple[FastMCP, Any]:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    provider = build_provider(settings)
    mcp = FastMCP(
        name="ClioAug22Build",
        instructions=INSTRUCTIONS,
        version=__version__,
    )
    register_clio_tools(mcp, provider)
    _register_http_routes(mcp, settings, provider)
    return mcp, provider


def _register_http_routes(mcp: FastMCP, settings: Settings, provider: Any) -> None:
    @mcp.custom_route("/health", methods=["GET"])
    async def health(_request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "service": "ClioAug22Build",
                "provider": settings.provider,
                "version": __version__,
            }
        )

    @mcp.custom_route("/ready", methods=["GET"])
    async def ready(_request: Request) -> JSONResponse:
        probe = {"ok": True, "clio_auth": "skipped"}
        if settings.has_clio_credentials and hasattr(provider, "health"):
            probe = await provider.health()
        status = 200 if probe.get("ok") or probe.get("clio_auth") == "skipped" else 503
        return JSONResponse(
            {
                "status": "ready" if status == 200 else "not_ready",
                "service": "ClioAug22Build",
                **probe,
            },
            status_code=status,
        )

    @mcp.custom_route("/", methods=["GET"])
    async def dashboard(_request: Request) -> HTMLResponse:
        return HTMLResponse(
            render_dashboard(
                {
                    "version": __version__,
                    "provider": settings.provider,
                    "transport": settings.mcp_transport,
                    "health": {"status": "ok"},
                    "credentials": {
                        "clio": settings.has_clio_credentials,
                        "mcp_http_api_key": bool(settings.mcp_http_api_key),
                    },
                    "tools": TOOL_CATALOG,
                }
            )
        )

    @mcp.custom_route("/oauth", methods=["GET", "POST"])
    async def oauth(request: Request) -> HTMLResponse:
        approval = "https://app.clio.com/oauth/approval"
        if request.method == "GET":
            return HTMLResponse(
                render_oauth_page(client_id=settings.clio_client_id or "")
            )
        form = await request.form()
        client_id = str(form.get("client_id") or "").strip()
        client_secret = str(form.get("client_secret") or "").strip()
        code = str(form.get("code") or "").strip()
        if not (client_id and client_secret and code):
            return HTMLResponse(
                render_oauth_page(
                    client_id=client_id,
                    code=code,
                    error="Client ID, Client Secret, and authorization code are all required.",
                ),
                status_code=400,
            )
        import httpx

        try:
            async with httpx.AsyncClient(timeout=20.0) as http:
                resp = await http.post(
                    f"{settings.clio_root}/oauth/token",
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": approval,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
        except Exception:
            logger.exception("Clio token exchange failed")
            return HTMLResponse(
                render_oauth_page(
                    client_id=client_id,
                    code=code,
                    error="Could not reach Clio. Try again in a minute.",
                ),
                status_code=502,
            )
        payload = {}
        try:
            payload = resp.json()
        except Exception:
            payload = {}
        refresh = str(payload.get("refresh_token") or "")
        if resp.status_code >= 400 or not refresh:
            logger.warning("Clio token exchange HTTP %s", resp.status_code)
            detail = payload.get("error_description") or payload.get("error") or f"HTTP {resp.status_code}"
            return HTMLResponse(
                render_oauth_page(
                    client_id=client_id,
                    code=code,
                    error=f"Clio rejected the exchange: {detail}",
                ),
                status_code=400,
            )
        logger.info("Clio refresh token issued")
        return HTMLResponse(
            render_oauth_page(
                client_id=client_id,
                refresh_token=refresh,
                access_note="Access token is short-lived; the server refreshes it automatically. Save only the refresh token.",
            )
        )



def run() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    mcp, _provider = create_mcp(settings)
    if settings.is_http:
        if not settings.mcp_http_api_key:
            logger.warning(
                "MCP_HTTP_API_KEY is empty; /mcp is open. Set it before putting this on the public internet."
            )
        middleware = []
        if settings.mcp_http_api_key:
            from starlette.middleware import Middleware

            middleware = [Middleware(BearerAuthMiddleware, api_key=settings.mcp_http_api_key)]
        logger.info(
            "Starting ClioAug22Build HTTP on %s:%s (path=/mcp)",
            settings.host,
            settings.port,
        )
        mcp.run(
            transport="http",
            host=settings.host,
            port=settings.port,
            path="/mcp",
            stateless_http=True,
            middleware=middleware,
            show_banner=False,
        )
    else:
        logger.info("Starting ClioAug22Build stdio")
        mcp.run(transport="stdio", show_banner=False)
