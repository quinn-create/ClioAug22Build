from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse


WRITE_METHODS = {"POST", "PATCH", "PUT"}


class PathSafetyError(ValueError):
    pass


def drop_none(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    return {k: v for k, v in data.items() if v is not None}


def wrap_body(body: Any, raw: bool = False) -> Any:
    """Auto-wrap Clio write bodies in {"data": ...} unless raw or already wrapped."""
    if raw or body is None:
        return body
    if isinstance(body, dict) and "data" in body:
        return body
    return {"data": body}


def hours_to_seconds(hours: float | int) -> int:
    return int(round(float(hours) * 3600))


def resolve_quantity_seconds(
    hours: float | int | None, quantity_seconds: int | None
) -> int:
    if quantity_seconds is not None:
        return int(quantity_seconds)
    if hours is not None:
        return hours_to_seconds(hours)
    raise ValueError("Provide hours or quantity_seconds")


def nest_id(value: int | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"id": int(value)}


def extract_page_token(next_url: str | None) -> str | None:
    if not next_url:
        return None
    parsed = urlparse(next_url)
    token = parse_qs(parsed.query).get("page_token")
    if token:
        return token[0]
    return next_url


def resource_from_path(path: str) -> str:
    trimmed = path.strip("/")
    if trimmed.startswith("api/v4/"):
        trimmed = trimmed[len("api/v4/") :]
    parts = [p for p in trimmed.split("/") if p]
    if not parts:
        return ""
    if len(parts) >= 2 and parts[0] == "users" and parts[1] == "who_am_i":
        return "users/who_am_i"
    return parts[0]


def normalize_clio_path(path: str, api_root: str) -> tuple[str, dict[str, str]]:
    """Return (absolute_url, extra_query) for a generic-tool path.

    Rejects off-host URLs and path traversal (SSRF protection).
    """
    if not path or not path.strip():
        raise PathSafetyError("path is required")
    path = path.strip()
    extra_query: dict[str, str] = {}
    api_parsed = urlparse(api_root)

    if path.startswith("http://") or path.startswith("https://"):
        parsed = urlparse(path)
        if parsed.scheme not in ("https",):
            raise PathSafetyError("only https URLs on the configured Clio host are allowed")
        if parsed.netloc.lower() != api_parsed.netloc.lower():
            raise PathSafetyError("path must stay on the configured Clio host")
        if ".." in parsed.path.split("/"):
            raise PathSafetyError("invalid path")
        extra_query = {k: v[-1] for k, v in parse_qs(parsed.query).items() if v}
        return path.split("?", 1)[0], extra_query

    if path.startswith("//") or ".." in path.split("/"):
        raise PathSafetyError("invalid path")
    if not path.startswith("/"):
        path = "/" + path
    if path.startswith("/api/v4"):
        rel = path[len("/api/v4") :] or "/"
    else:
        rel = path
    url = urljoin(api_root.rstrip("/") + "/", rel.lstrip("/"))
    parsed = urlparse(url)
    if parsed.netloc.lower() != api_parsed.netloc.lower():
        raise PathSafetyError("path escaped the configured Clio host")
    return url, extra_query


def paging_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"has_next": False, "next_page_token": None}
    meta = payload.get("meta") or {}
    paging = meta.get("paging") or {}
    next_url = paging.get("next")
    return {
        "has_next": bool(next_url),
        "next_page_token": extract_page_token(next_url),
    }


def ok(data: Any, *, paging: dict[str, Any] | None = None, warning: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": True, "data": data}
    if paging:
        result["paging"] = paging
    if warning:
        result["warning"] = warning
    return result


def fail(
    status: int,
    error: str,
    message: str,
    hint: str | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "status": status,
        "error": error,
        "message": message,
    }
    if hint:
        result["hint"] = hint
    return result
