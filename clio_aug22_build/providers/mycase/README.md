# Adding a MyCase provider later

v1 ships Clio only. This folder exists so a second practice-management adapter
can be added without rewriting `server.py` or the MCP tool registration.

## How to add MyCase

1. Implement `MycaseProvider` against `PracticeManagementProvider` in
   `clio_aug22_build/providers/base.py`.
2. Put HTTP/auth in `providers/mycase/client.py` (do **not** reuse Clio
   envelope/pagination helpers — MyCase is a different API).
3. Register MCP tools as `mycase_*` (do not rename `clio_*`).
4. Switch with `PROVIDER=mycase`, or run a second process.
5. Env vars should be `MYCASE_*`, never mixed into `CLIO_*`.

Do not invent a fake unified `pms_*` tool layer. Agents need to see each
vendor's quirks.
