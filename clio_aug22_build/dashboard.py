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
        <p class="note">Looks only for whether CLIO_CLIENT_ID / SECRET / REFRESH_TOKEN are set. Values are never shown. Need a refresh token? Use the <a href="/oauth">token helper</a>.</p>
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


def render_oauth_page(
    *,
    client_id: str = "",
    code: str = "",
    error: str = "",
    refresh_token: str = "",
    access_note: str = "",
) -> str:
    cid = escape(client_id)
    code_val = escape(code)
    err = escape(error)
    token = escape(refresh_token)
    note = escape(access_note)
    err_html = f'<p class="err">{err}</p>' if error else ""
    token_html = (
        f"""
        <div class="card okbox">
          <h2>Refresh token</h2>
          <p class="note">Copy this into Railway → Variables → <code>CLIO_REFRESH_TOKEN</code>. Do not put it in chat.</p>
          <textarea readonly rows="4">{token}</textarea>
          <p class="note">{note}</p>
        </div>
        """
        if refresh_token
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Get Clio refresh token</title>
  <style>
    :root {{ --bg:#0b1220; --card:#141c2e; --line:#243049; --gold:#c9a227; --text:#e8eef7; --muted:#8b9bb4; --ok:#3dd68c; --bad:#f07178; }}
    body {{ margin:0; font-family: Georgia, serif; background: #0b1220; color: var(--text); }}
    main {{ max-width: 640px; margin: 0 auto; padding: 22px; }}
    h1 {{ font-size: 24px; }}
    h1 span {{ color: var(--gold); }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; margin: 14px 0; }}
    h2 {{ margin: 0 0 10px; font-size: 13px; letter-spacing: .14em; text-transform: uppercase; color: var(--gold); }}
    label {{ display:block; font-size:13px; color: var(--muted); margin: 10px 0 4px; }}
    input, textarea {{ width:100%; background:#0b1220; color:var(--text); border:1px solid var(--line); border-radius:8px; padding:10px; font-family: ui-monospace, Menlo, monospace; font-size: 14px; }}
    button {{ display:inline-block; margin-top:12px; background: var(--gold); color:#0b1220; border:0; border-radius:8px; padding:12px 16px; font-weight:700; }}
    .note {{ color: var(--muted); font-size: 14px; line-height: 1.5; }}
    .err {{ color: var(--bad); }}
    .okbox {{ border-color: var(--ok); }}
    ol {{ line-height: 1.6; }}
    a {{ color: var(--gold); }}
  </style>
</head>
<body>
<main>
  <h1>Clio <span>refresh token</span></h1>
  <p class="note"><a href="/">Back to dashboard</a></p>
  {err_html}
  {token_html}
  <div class="card">
    <h2>Step 1 — Open Clio</h2>
    <p class="note">Paste your Client ID, tap the button, then Allow the app. You will land on a Clio page whose title looks like <code>Success code=...</code>.</p>
    <form method="get" action="https://app.clio.com/oauth/authorize">
      <input type="hidden" name="response_type" value="code"/>
      <input type="hidden" name="redirect_uri" value="https://app.clio.com/oauth/approval"/>
      <label>Clio Client ID</label>
      <input name="client_id" value="{cid}" autocomplete="off" required/>
      <button type="submit">Open Clio and allow access</button>
    </form>
  </div>
  <div class="card">
    <h2>Step 2 — Exchange the code</h2>
    <p class="note">Copy the <code>code</code> from the Clio success page (the long string after <code>code=</code> in the address bar). Paste it below with your Client ID and Secret.</p>
    <form method="post" action="/oauth">
      <label>Clio Client ID</label>
      <input name="client_id" value="{cid}" autocomplete="off" required/>
      <label>Clio Client Secret</label>
      <input name="client_secret" type="password" autocomplete="off" required/>
      <label>Authorization code</label>
      <input name="code" value="{code_val}" autocomplete="off" required/>
      <button type="submit">Get refresh token</button>
    </form>
  </div>
  <div class="card">
    <h2>Step 3 — Save it in Railway</h2>
    <ol>
      <li>Railway → your service → <b>Variables</b></li>
      <li>Set <code>CLIO_CLIENT_ID</code>, <code>CLIO_CLIENT_SECRET</code>, <code>CLIO_REFRESH_TOKEN</code></li>
      <li>Save and wait for a green deploy</li>
      <li>The dashboard should then say <b>env present</b></li>
    </ol>
  </div>
</main>
</body>
</html>
"""

