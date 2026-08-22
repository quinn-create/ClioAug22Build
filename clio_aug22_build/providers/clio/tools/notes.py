from __future__ import annotations

from typing import Any, Literal, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_list_notes")
    async def clio_list_notes(
        note_type: Literal["Matter", "Contact"],
        matter_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """List notes. note_type is REQUIRED by Clio (Matter or Contact).

        ALWAYS list before clio_create_note. Prefer this over clio_api_request GET /notes.
        """
        return await provider.list_notes(
            note_type=note_type,
            matter_id=matter_id,
            contact_id=contact_id,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_create_note")
    async def clio_create_note(
        note_type: Literal["Matter", "Contact"],
        detail: str,
        matter_id: Optional[int] = None,
        contact_id: Optional[int] = None,
        subject: Optional[str] = None,
        date: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a note. Matter notes need matter_id; Contact notes need contact_id.

        ALWAYS list notes on that record first. date is YYYY-MM-DD.
        """
        return await provider.create_note(
            note_type=note_type,
            detail=detail,
            matter_id=matter_id,
            contact_id=contact_id,
            subject=subject,
            date=date,
        )

    @mcp.tool(name="clio_update_note")
    async def clio_update_note(
        note_id: int,
        detail: Optional[str] = None,
        subject: Optional[str] = None,
        date: Optional[str] = None,
    ) -> dict[str, Any]:
        """PATCH an existing note. Do not create a second note to correct one."""
        return await provider.update_note(
            note_id=note_id, detail=detail, subject=subject, date=date
        )
