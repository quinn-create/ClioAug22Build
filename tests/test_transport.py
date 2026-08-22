from __future__ import annotations

from clio_aug22_build.config import Settings


def test_default_transport_is_stdio(monkeypatch) -> None:
    for name in (
        "MCP_TRANSPORT",
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_ENVIRONMENT_ID",
        "RAILWAY_PROJECT_ID",
        "RAILWAY_SERVICE_ID",
    ):
        monkeypatch.delenv(name, raising=False)
    settings = Settings()
    assert settings.mcp_transport == "stdio"
    assert settings.is_http is False


def test_railway_forces_http_even_if_stdio(monkeypatch) -> None:
    monkeypatch.setenv("MCP_TRANSPORT", "stdio")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    settings = Settings()
    assert settings.mcp_transport == "http"
    assert settings.is_http is True
