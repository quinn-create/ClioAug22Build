from __future__ import annotations

import hashlib
import logging
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from clio_aug22_build.config import Settings

logger = logging.getLogger(__name__)

_CODES: dict[str, dict[str, Any]] = {}
CODE_TTL_SEC = 300


def public_base(request: Request) -> str:
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme or "https"
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto}://{host}".rstrip("/")


def _pkce_s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    import base64

    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def _purge() -> None:
    now = time.time()
    dead = [k for k, v in _CODES.items() if v.get("exp", 0) < now]
    for k in dead:
        _CODES.pop(k, None)


def well_known_authorization_server(request: Request) -> JSONResponse:
    base = public_base(request)
    return JSONResponse(
        {
            "issuer": base,
            "authorization_endpoint": f"{base}/mcp-auth/authorize",
            "token_endpoint": f"{base}/mcp-auth/token",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "code_challenge_methods_supported": ["S256", "plain"],
            "token_endpoint_auth_methods_supported": ["none"],
            "scopes_supported": ["mcp"],
        }
    )


def well_known_protected_resource(request: Request) -> JSONResponse:
    base = public_base(request)
    return JSONResponse(
        {
            "resource": f"{base}/mcp",
            "authorization_servers": [base],
            "bearer_methods_supported": ["header"],
            "scopes_supported": ["mcp"],
        }
    )


def _authorize_html(*, error: str = "", client_id: str = "") -> str:
    err = f'<p class="err">{error}</p>' if error else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Allow Grok</title>
<style>
  body {{ margin:0; background:#0b1220; color:#e8eef7; font-family: Georgia, serif; }}
  main {{ max-width:520px; margin:0 auto; padding:28px 18px; }}
  h1 {{ font-size:24px; }} h1 span {{ color:#c9a227; }}
  .card {{ background:#141c2e; border:1px solid #243049; border-radius:14px; padding:18px; }}
  label {{ display:block; color:#8b9bb4; font-size:13px; margin:12px 0 6px; }}
  input {{ width:100%; box-sizing:border-box; background:#0b1220; color:#e8eef7; border:1px solid #243049; border-radius:8px; padding:10px; }}
  button {{ margin-top:16px; background:#c9a227; color:#0b1220; border:0; border-radius:8px; padding:12px 16px; font-weight:700; width:100%; }}
  .note {{ color:#8b9bb4; font-size:14px; line-height:1.5; }}
  .err {{ color:#f07178; }}
</style></head>
<body><main>
  <h1>Allow <span>Grok</span></h1>
  <p class="note">This is <b>not</b> your Clio Client ID. Paste the Railway variable <code>MCP_HTTP_API_KEY</code>.</p>
  {err}
  <div class="card">
    <form method="post">
      <label>MCP_HTTP_API_KEY (from Railway → Variables)</label>
      <input type="password" name="api_key" autocomplete="off" required/>
      <button type="submit">Allow Grok to use ClioAug22Build</button>
    </form>
  </div>
</main></body></html>"""


async def authorize_get(request: Request) -> Response:
    q = request.query_params
    if not q.get("redirect_uri") or q.get("response_type", "code") != "code":
        return HTMLResponse(
            _authorize_html(error="Open this page from Grok’s Save & Connect. Don’t load it directly.")
        )
    return HTMLResponse(_authorize_html())


async def authorize_post(request: Request, settings: Settings) -> Response:
    q = request.query_params
    form = await request.form()
    api_key = str(form.get("api_key") or "").strip()
    redirect_uri = (q.get("redirect_uri") or "").strip()
    state = q.get("state") or ""
    challenge = q.get("code_challenge") or ""
    method = (q.get("code_challenge_method") or "plain").lower()

    if not settings.mcp_http_api_key or api_key != settings.mcp_http_api_key:
        return HTMLResponse(
            _authorize_html(error="That key does not match Railway MCP_HTTP_API_KEY."),
            status_code=401,
        )
    if not redirect_uri.startswith("https://"):
        return HTMLResponse(_authorize_html(error="Invalid redirect."), status_code=400)

    _purge()
    code = secrets.token_urlsafe(24)
    _CODES[code] = {
        "exp": time.time() + CODE_TTL_SEC,
        "redirect_uri": redirect_uri,
        "challenge": challenge,
        "method": method,
        "access_token": settings.mcp_http_api_key,
    }
    logger.info("Grok OAuth code issued")
    params = {"code": code}
    if state:
        params["state"] = state
    sep = "&" if "?" in redirect_uri else "?"
    return RedirectResponse(redirect_uri + sep + urlencode(params), status_code=302)


async def token_post(request: Request) -> Response:
    form = await request.form()
    code = str(form.get("code") or "").strip()
    verifier = str(form.get("code_verifier") or "").strip()
    redirect_uri = str(form.get("redirect_uri") or "").strip()
    _purge()
    row = _CODES.pop(code, None)
    if not row:
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    if redirect_uri and row.get("redirect_uri") and redirect_uri != row["redirect_uri"]:
        return JSONResponse({"error": "invalid_grant"}, status_code=400)
    challenge = row.get("challenge") or ""
    if challenge:
        method = row.get("method") or "plain"
        computed = _pkce_s256(verifier) if method == "s256" else verifier
        if not verifier or computed != challenge:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)
    return JSONResponse(
        {
            "access_token": row["access_token"],
            "token_type": "bearer",
            "expires_in": 60 * 60 * 24 * 365,
            "scope": "mcp",
        }
    )
