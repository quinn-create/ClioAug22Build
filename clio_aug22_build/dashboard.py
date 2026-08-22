from __future__ import annotations

from html import escape
from typing import Any


def render_dashboard(payload: dict[str, Any]) -> str:
    creds = payload.get("credentials") or {}
    tools = payload.get("tools") or []
    health = payload.get("health") or {}
    transport = escape(str(payload.get("transport") or ""))
    provider = escape(str(payload.get("provider") or ""))
    version = escape(str(payload.get("version") or ""))
    clio_ok = bool(creds.get("clio"))
    key_ok = bool(creds.get("mcp_http_api_key"))
    http = str(payload.get("transport") or "") in ("http", "streamable-http")

    def pill(ok: bool, yes: str, no: str) -> str:
        cls = "ok" if ok else "warn"
        return f'<span class="pill {cls}">{escape(yes if ok else no)}</span>'

    tool_rows = "".join(
        f"<tr><td><code>{escape(t['name'])}</code></td><td>{escape(t['summary'])}</td></tr>"
        for t in tools
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ClioAug22Build</title>
  <style>
    :root {{
      --bg: #0b1220;
      --card: #141c2e;
      --line: #243049;
      --gold: #c9a227;
      --text: #e8eef7;
      --muted: #8b9bb4;
      --ok: #3dd68c;
      --warn: #f0c14b;
      --bad: #f07178;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1a2744, var(--bg));
      color: var(--text); min-height: 100vh;
    }}
    header {{
      padding: 28px 22px 12px; border-bottom: 1px solid var(--line);
      display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; align-items: flex-end;
    }}
    h1 {{ margin: 0; font-size: 28px; letter-spacing: 0.04em; }}
    h1 span {{ color: var(--gold); }}
    .sub {{ color: var(--muted); font-size: 14px; margin-top: 6px; }}
    main {{ padding: 22px; max-width: 1100px; margin: 0 auto; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; }}
    @media (min-width: 760px) {{
      .grid {{ grid-template-columns: repeat(3, 1fr); }}
    }}
    .card {{
      background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px;
    }}
    h2 {{ margin: 0 0 10px; font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--gold); }}
    .pill {{ display: inline-block; border-radius: 999px; padding: 4px 10px; font-size: 12px; font-family: ui-monospace, Menlo, monospace; }}
    .pill.ok {{ background: #163528; color: var(--ok); }}
    .pill.warn {{ background: #3a2a12; color: var(--warn); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    td, th {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    code {{ font-family: ui-monospace, Menlo, monospace; color: #d7e3ff; font-size: 12px; }}
    .note {{ color: var(--muted); font-size: 13px; line-height: 1.5; }}
    a {{ color: var(--gold); }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Clio<span>Aug22</span>Build</h1>
      <div class="sub">Production MCP server for Clio Manage · v{version} · provider {provider} · {transport}</div>
    </div>
    <div>{pill(health.get("status") == "ok", "health ok", "health down")}</div>
  </header>
  <main>
    <div class="grid">
      <section class="card">
        <h2>Clio credentials</h2>
        {pill(clio_ok, "env present", "env missing")}
        <p class="note">Looks only for whether CLIO_CLIENT_ID / SECRET / REFRESH_TOKEN are set. Values are never shown.</p>
      </section>
      <section class="card">
        <h2>HTTP MCP key</h2>
        {pill((key_ok or not http), "protected" if key_ok else "stdio / open preview", "missing — set MCP_HTTP_API_KEY")}
        <p class="note">Streamable HTTP at <code>/mcp</code>. Health at <code>/health</code> stays public.</p>
      </section>
      <section class="card">
        <h2>Connect</h2>
        <p class="note">Claude Desktop / Cursor: stdio. Railway / Grok / n8n: Streamable HTTP with Bearer token. Copy snippets from the README.</p>
      </section>
    </div>
    <section class="card" style="margin-top:16px">
      <h2>Tools ({len(tools)})</h2>
      <p class="note">Find/list before every create. Specialized tools beat <code>clio_api_request</code>. POST/PATCH bodies auto-wrap in <code>{{"data": ...}}</code> unless <code>raw=true</code>.</p>
      <table>
        <thead><tr><th>Tool</th><th>When to use</th></tr></thead>
        <tbody>{tool_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


TOOL_CATALOG = [
    {"name": "clio_who_am_i", "summary": "Authenticated Clio user. Call first for your user id."},
    {"name": "clio_find_contacts", "summary": "Search people/companies. Always before create."},
    {"name": "clio_get_contact", "summary": "Get one contact by id."},
    {"name": "clio_create_person", "summary": "Create a Person after find returned nothing."},
    {"name": "clio_create_company", "summary": "Create a Company after find returned nothing."},
    {"name": "clio_update_contact", "summary": "PATCH an existing person or company."},
    {"name": "clio_find_matters", "summary": "Search matters. Always before create."},
    {"name": "clio_get_matter", "summary": "Get one matter by id."},
    {"name": "clio_create_matter", "summary": "Create a matter for an existing client."},
    {"name": "clio_update_matter", "summary": "PATCH status, description, attorney, dates."},
    {"name": "clio_list_calendar_entries", "summary": "List entries in a required date window."},
    {"name": "clio_create_calendar_entry", "summary": "Create after listing the same window."},
    {"name": "clio_update_calendar_entry", "summary": "PATCH an existing calendar entry."},
    {"name": "clio_list_tasks", "summary": "List tasks by matter, assignee, or status."},
    {"name": "clio_create_task", "summary": "Create after listing; skip duplicate names."},
    {"name": "clio_update_task", "summary": "PATCH status, due date, assignee."},
    {"name": "clio_list_activities", "summary": "List time entries before logging time."},
    {"name": "clio_create_time_entry", "summary": "Log hours (or seconds). Flat fee via custom_rate."},
    {"name": "clio_update_time_entry", "summary": "PATCH unbilled time. Billed entries 403."},
    {"name": "clio_list_notes", "summary": "List notes. type Matter or Contact is required."},
    {"name": "clio_create_note", "summary": "Create after listing that record's notes."},
    {"name": "clio_update_note", "summary": "PATCH an existing note."},
    {"name": "clio_list_documents", "summary": "List files + 3-step upload guidance. No binary upload."},
    {"name": "clio_api_request", "summary": "Generic fallback. Auto-wraps {data} unless raw=true."},
]
