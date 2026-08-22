# ClioAug22Build

Production MCP server for **your** Clio Manage account.

- Python + FastMCP
- Dual transport: **stdio** (Claude Desktop / Cursor / Claude Code) and **Streamable HTTP** (Railway, Grok, n8n)
- Automatic Clio access-token refresh (30-day access token; refresh token does not expire or rotate)
- Specialized tools for contacts, matters, calendar, tasks, time, notes, documents
- Mandatory generic tool `clio_api_request` with auto `{"data": ...}` wrapping (`raw=true` to skip)

v1 is single-user. A MyCase adapter can be added later without a rewrite (`providers/mycase/`).

---

## What you need before starting

You already have these from the Clio Developer Portal. Keep them off chat logs if you can; put them in Railway / a local `.env` file.

1. **CLIO_CLIENT_ID**
2. **CLIO_CLIENT_SECRET**
3. **CLIO_REFRESH_TOKEN** (long-lived)

US region is the default (`https://app.clio.com`). If your firm is on EU / CA / AU, change `CLIO_BASE_URL`.

You will also make one extra secret for the public HTTP URL:

4. **MCP_HTTP_API_KEY** — a long random string. Anyone who has this and your Railway URL can read/write your entire Clio account.

Generate one (Mac/Linux):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 1. Local folder (one time)

On your Mac, in Terminal:

```bash
cd ~/Desktop
# If you already have this folder from git, skip the clone and cd into it instead.
cd ClioAug22Build
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Open `.env` in TextEdit and paste your three Clio values plus `MCP_HTTP_API_KEY`. Save.

Do **not** email `.env`. Do **not** commit it.

### Run tests (no Clio account needed)

```bash
source .venv/bin/activate
pytest -q
```

You want a green pass.

### Run locally over HTTP (optional smoke)

```bash
source .venv/bin/activate
export MCP_TRANSPORT=http
export PORT=8080
python -m clio_aug22_build
```

In a second Terminal:

```bash
curl http://127.0.0.1:8080/health
```

You should see `"status":"ok"` and `"service":"ClioAug22Build"`.

Stop the server with Ctrl+C.

### Run locally over stdio (what Claude Desktop uses)

Claude Desktop starts this for you. You do not run it by hand unless testing.

---

## 2. Docker on your Mac (optional)

```bash
cd ~/Desktop/ClioAug22Build
docker build -t clioaug22build .
docker run --rm -p 8080:8080 --env-file .env -e MCP_TRANSPORT=http clioaug22build
```

Then:

```bash
curl http://127.0.0.1:8080/health
```

---

## 3. Deploy to Railway (this is the production copy)

1. Create a GitHub repo named `ClioAug22Build` and push this folder (without `.env`).
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo → pick `ClioAug22Build`.
3. Railway will detect the Dockerfile.
4. Open **Variables** and add exactly these (paste your real values):

```
CLIO_CLIENT_ID=paste
CLIO_CLIENT_SECRET=paste
CLIO_REFRESH_TOKEN=paste
CLIO_BASE_URL=https://app.clio.com
CLIO_API_VERSION=4.0.0
PROVIDER=clio
MCP_TRANSPORT=http
MCP_HTTP_API_KEY=paste-the-random-string
LOG_LEVEL=INFO
```

5. Settings → generate a public domain (example: `https://clioaug22build-production.up.railway.app`).
6. Healthcheck path: `/health` (already in `railway.toml`).
7. Wait until the deploy is **Success**.
8. In a browser open `https://YOUR_RAILWAY_URL/health`. You should see `"status":"ok"`.
9. Open `https://YOUR_RAILWAY_URL/` — you should see the ClioAug22Build dashboard. It will show whether Clio env vars are present (not the values).

If `/health` works but tools fail, the three Clio secrets are wrong or issued for a different region.

---

## 4. Connect clients

Replace `YOUR_RAILWAY_URL` (no trailing slash) and `YOUR_MCP_HTTP_API_KEY`.

### Claude Desktop — remote Railway (recommended)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` on Mac.

```json
{
  "mcpServers": {
    "ClioAug22Build": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://YOUR_RAILWAY_URL/mcp",
        "--header",
        "Authorization: Bearer YOUR_MCP_HTTP_API_KEY"
      ]
    }
  }
}
```

Quit Claude Desktop fully (Cmd+Q) and reopen. You should see `ClioAug22Build` under tools. Ask: “Call clio_who_am_i”.

### Claude Desktop — local stdio via Docker

```json
{
  "mcpServers": {
    "ClioAug22Build": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "CLIO_CLIENT_ID",
        "-e", "CLIO_CLIENT_SECRET",
        "-e", "CLIO_REFRESH_TOKEN",
        "-e", "MCP_TRANSPORT=stdio",
        "clioaug22build"
      ],
      "env": {
        "CLIO_CLIENT_ID": "paste",
        "CLIO_CLIENT_SECRET": "paste",
        "CLIO_REFRESH_TOKEN": "paste"
      }
    }
  }
}
```

### Claude Code

In `~/.claude.json` (or project `.mcp.json`):

```json
{
  "mcpServers": {
    "ClioAug22Build": {
      "command": "python",
      "args": ["-m", "clio_aug22_build"],
      "cwd": "/FULL/PATH/TO/ClioAug22Build",
      "env": {
        "MCP_TRANSPORT": "stdio",
        "CLIO_CLIENT_ID": "paste",
        "CLIO_CLIENT_SECRET": "paste",
        "CLIO_REFRESH_TOKEN": "paste"
      }
    }
  }
}
```

Use the venv python if you created one: `/FULL/PATH/TO/ClioAug22Build/.venv/bin/python`.

### Cursor

Cursor Settings → MCP → add:

```json
{
  "mcpServers": {
    "ClioAug22Build": {
      "url": "https://YOUR_RAILWAY_URL/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_HTTP_API_KEY"
      }
    }
  }
}
```

### Grok custom MCP / connector

- URL: `https://YOUR_RAILWAY_URL/mcp`
- Transport: **Streamable HTTP**
- Header: `Authorization` = `Bearer YOUR_MCP_HTTP_API_KEY`

---

## 5. Tool list (24)

Always **find/list before create**.

| Tool | Use |
|---|---|
| `clio_who_am_i` | Your Clio user id |
| `clio_find_contacts` / `clio_get_contact` | Search / get |
| `clio_create_person` / `clio_create_company` | Create after find missed |
| `clio_update_contact` | PATCH existing |
| `clio_find_matters` / `clio_get_matter` | Search / get |
| `clio_create_matter` / `clio_update_matter` | Create / PATCH |
| `clio_list_calendar_entries` | Required date window |
| `clio_create_calendar_entry` / `clio_update_calendar_entry` | Create / PATCH |
| `clio_list_tasks` / `clio_create_task` / `clio_update_task` | Tasks |
| `clio_list_activities` | Time entries |
| `clio_create_time_entry` / `clio_update_time_entry` | Hours or seconds; flat fee via `custom_rate` |
| `clio_list_notes` / `clio_create_note` / `clio_update_note` | `note_type` is required (`Matter` or `Contact`) |
| `clio_list_documents` | Metadata + upload recipe (no binary upload in v1) |
| `clio_api_request` | Anything else |

### Generic tool envelope

`clio_api_request` for POST/PATCH/PUT:

- **`raw=false` (default):** wraps your body in `{"data": {...}}`. If you already sent `{"data": {...}}`, it is **not** double-wrapped.
- **`raw=true`:** sends the body exactly. Use this only when you need to bypass wrapping.

---

## 6. Clio quirks this server already handles

- Missing `fields=` would otherwise return only `id` and `etag`. Specialized tools send a default field set.
- Nested fields: `matter{id,description}` is OK. Second-level nesting 400s.
- Pagination: 200 max per page, cursor `page_token`. `auto_page` is capped at 5 pages.
- Time `quantity` is **seconds**. Specialized tools accept `hours` and convert.
- Flat fee: `custom_rate` is the top of Clio’s rate hierarchy. Typical recipe: `custom_rate=500`, `hours=1`.
- Nested IDs: tools take `matter_id=123` and send `{"matter": {"id": 123}}`.
- Notes list requires `type`.
- Contact email/phone are arrays; create_person wraps a simple string for you.
- Access token lasts 30 days; refresh token is reused (Clio does not rotate it).
- 401 → one forced refresh + retry.
- 429 → honor `Retry-After` (default budget ~50 req/min).
- Documents: list only + 3-step upload guidance (`put_url`).

---

## 7. Security

- Tokens never logged (Bearer / refresh_token / client_secret are redacted).
- Docker runs as non-root user `mcp` (uid 10001).
- HTTP `/mcp` requires `Authorization: Bearer $MCP_HTTP_API_KEY`.
- `/health` is public on purpose (Railway healthcheck).
- Generic tool cannot call hosts other than your Clio region.
- This server **is you**. Treat the Railway URL + API key like a master Clio password.

---

## 8. Live Clio verification (after secrets are in)

Ask the connected agent, in order:

1. `clio_who_am_i`
2. `clio_find_contacts` query `Rodriguez` — expect existing hits, **do not create**
3. Create a uniquely named test person `MCP Probe YYYYMMDD`
4. Find that name — exactly one hit
5. Update their phone
6. Create a matter `MCP Probe Matter` on that contact
7. Find it — one hit
8. Create a task, list it, mark complete
9. List calendar today, create `MCP Probe`, list again, update the time
10. Log 0.1 hours with note `MCP probe`
11. Flat-fee probe: `custom_rate=1`, `hours=1`, note `MCP flat probe`
12. Create a Matter note, list notes
13. `clio_list_documents` on a real matter — names, not just id/etag
14. `clio_api_request` GET `/users/who_am_i`
15. POST with `raw=false` and an unwrapped body — should succeed
16. Same POST with `raw=true` and unwrapped body — Clio 400 (proves raw skips wrap)

Cleanup: rename probe records `ZZZ-DELETE-*` and close the probe matter. This server does not auto-delete.

---

## 9. Project layout

```
ClioAug22Build/
  clio_aug22_build/          # Python package
    server.py                # FastMCP + /health + /mcp
    providers/clio/          # Clio HTTP, token, tools
    providers/mycase/        # stub for later
  tests/
  Dockerfile
  railway.toml
  .env.example
```

---

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `/health` fails on Railway | Image didn't boot. Check Railway logs for Python traceback. |
| Tools say missing credentials | Variables not set, or set on the wrong Railway service. |
| `Clio rejected the token` | Wrong secret, or token is for a different region. |
| Claude doesn't show the server | JSON comma error in config, or didn't fully quit Claude. |
| HTTP 401 from `/mcp` | Missing/wrong `Authorization: Bearer ...` |
| Empty records (only id/etag) | You called the generic tool without `fields`. Use a specialized tool. |
| 429 | Slow down. Default Clio budget is ~50 requests/minute. |
| Create made a duplicate | Find/list first. The tool descriptions require it; the model can still ignore them. |
