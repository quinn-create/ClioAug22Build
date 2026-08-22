from __future__ import annotations

from typing import Any

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_who_am_i")
    async def clio_who_am_i() -> dict[str, Any]:
        """Return the authenticated Clio user (id, name, email, timezone, roles).

        Call this first in a session when you need your user id for assignees
        or timekeepers. Prefer this over clio_api_request GET /users/who_am_i.
        """
        return await provider.who_am_i()
