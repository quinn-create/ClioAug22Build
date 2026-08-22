from __future__ import annotations

import logging
import re
from typing import Any

_BEARER = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)
_ASSIGNED = re.compile(
    r"(?i)(access_token|refresh_token|client_secret|client_id|api[_-]?key"
    r"|authorization|mcp_http_api_key|clio_refresh_token|clio_client_secret"
    r"|clio_client_id)\s*[:=]\s*([^\s,;]+)"
)
_JSON_SECRET = re.compile(
    r'(?i)("(access_token|refresh_token|client_secret|client_id)"\s*:\s*")[^"]+(")'
)


def redact(text: str) -> str:
    if not text:
        return text
    text = _BEARER.sub(r"\1[REDACTED]", text)
    text = _ASSIGNED.sub(r"\1=[REDACTED]", text)
    text = _JSON_SECRET.sub(r"\1[REDACTED]\3", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _redact_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(_redact_value(a) for a in record.args)
        if record.exc_text:
            record.exc_text = redact(record.exc_text)
        return True


def _redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact(value)
    return value


def setup_logging(level: str = "INFO") -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root.addHandler(handler)
    redactor = RedactingFilter()
    for handler in root.handlers:
        handler.addFilter(redactor)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
