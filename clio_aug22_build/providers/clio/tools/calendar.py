from __future__ import annotations

from typing import Any, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_list_calendar_entries")
    async def clio_list_calendar_entries(
        from_datetime: str,
        to_datetime: str,
        matter_id: Optional[int] = None,
        query: Optional[str] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """List calendar entries in a required date window (ISO-8601 from_datetime / to_datetime).

        ALWAYS list the window before clio_create_calendar_entry so you do not double-book.
        Prefer this over clio_api_request GET /calendar_entries.
        """
        return await provider.list_calendar_entries(
            from_datetime=from_datetime,
            to_datetime=to_datetime,
            matter_id=matter_id,
            query=query,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_create_calendar_entry")
    async def clio_create_calendar_entry(
        summary: str,
        start_at: str,
        end_at: str,
        all_day: bool = False,
        description: Optional[str] = None,
        location: Optional[str] = None,
        matter_id: Optional[int] = None,
        attendee_user_ids: Optional[list[int]] = None,
    ) -> dict[str, Any]:
        """Create a calendar entry. ALWAYS list the same window first.

        start_at and end_at are ISO-8601 datetimes. Skip create if the same summary+start already exists.
        """
        return await provider.create_calendar_entry(
            summary=summary,
            start_at=start_at,
            end_at=end_at,
            all_day=all_day,
            description=description,
            location=location,
            matter_id=matter_id,
            attendee_user_ids=attendee_user_ids,
        )

    @mcp.tool(name="clio_update_calendar_entry")
    async def clio_update_calendar_entry(
        entry_id: int,
        summary: Optional[str] = None,
        start_at: Optional[str] = None,
        end_at: Optional[str] = None,
        all_day: Optional[bool] = None,
        description: Optional[str] = None,
        location: Optional[str] = None,
        matter_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """PATCH an existing calendar entry. Do not create a second entry to reschedule."""
        return await provider.update_calendar_entry(
            entry_id=entry_id,
            summary=summary,
            start_at=start_at,
            end_at=end_at,
            all_day=all_day,
            description=description,
            location=location,
            matter_id=matter_id,
        )
