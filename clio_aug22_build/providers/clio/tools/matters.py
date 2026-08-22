from __future__ import annotations

from typing import Any, Literal, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_find_matters")
    async def clio_find_matters(
        query: Optional[str] = None,
        client_id: Optional[int] = None,
        status: Optional[Literal["Open", "Pending", "Closed"]] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """Search matters. ALWAYS call this before clio_create_matter.

        Filter by client_id and status (Open/Pending/Closed). Prefer this over
        clio_api_request GET /matters.
        """
        return await provider.find_matters(
            query=query,
            client_id=client_id,
            status=status,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_get_matter")
    async def clio_get_matter(
        matter_id: int,
        fields: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get one matter by id."""
        return await provider.get_matter(matter_id=matter_id, fields=fields)

    @mcp.tool(name="clio_create_matter")
    async def clio_create_matter(
        client_id: int,
        description: str,
        status: Literal["Open", "Pending", "Closed"] = "Open",
        open_date: Optional[str] = None,
        practice_area_id: Optional[int] = None,
        responsible_attorney_id: Optional[int] = None,
        billable: bool = True,
    ) -> dict[str, Any]:
        """Create a matter. The client contact MUST already exist (find or create it first).

        ALWAYS clio_find_matters for that client + description first. Default status is Open.
        open_date is YYYY-MM-DD.
        """
        return await provider.create_matter(
            client_id=client_id,
            description=description,
            status=status,
            open_date=open_date,
            practice_area_id=practice_area_id,
            responsible_attorney_id=responsible_attorney_id,
            billable=billable,
        )

    @mcp.tool(name="clio_update_matter")
    async def clio_update_matter(
        matter_id: int,
        description: Optional[str] = None,
        status: Optional[Literal["Open", "Pending", "Closed"]] = None,
        close_date: Optional[str] = None,
        responsible_attorney_id: Optional[int] = None,
        billable: Optional[bool] = None,
        practice_area_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """PATCH an existing matter (status, description, attorney, close_date YYYY-MM-DD)."""
        return await provider.update_matter(
            matter_id=matter_id,
            description=description,
            status=status,
            close_date=close_date,
            responsible_attorney_id=responsible_attorney_id,
            billable=billable,
            practice_area_id=practice_area_id,
        )
