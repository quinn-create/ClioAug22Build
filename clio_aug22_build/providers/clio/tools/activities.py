from __future__ import annotations

from typing import Any, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_list_activities")
    async def clio_list_activities(
        matter_id: Optional[int] = None,
        user_id: Optional[int] = None,
        activity_type: Optional[str] = "TimeEntry",
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """List time/expense activities. ALWAYS list before clio_create_time_entry.

        date_from/date_to are YYYY-MM-DD and filter the returned page. Prefer this over
        clio_api_request GET /activities. Default activity_type is TimeEntry.
        """
        return await provider.list_activities(
            matter_id=matter_id,
            user_id=user_id,
            activity_type=activity_type,
            date_from=date_from,
            date_to=date_to,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_create_time_entry")
    async def clio_create_time_entry(
        date: str,
        matter_id: int,
        note: str,
        hours: Optional[float] = None,
        quantity_seconds: Optional[int] = None,
        user_id: Optional[int] = None,
        custom_rate: Optional[float] = None,
        flat_rate: Optional[bool] = None,
        price: Optional[float] = None,
        non_billable: Optional[bool] = None,
    ) -> dict[str, Any]:
        """Create a TimeEntry. ALWAYS clio_list_activities for that matter+date first.

        Pass hours (friendly, e.g. 0.3) OR quantity_seconds. If both are sent, seconds win.
        Clio stores quantity in SECONDS (1.5 hours = 5400).

        Flat fee: set custom_rate to the dollar amount and hours=1 (custom rate sits at the
        top of Clio's rate hierarchy). Alternatively flat_rate=true with price=the fee.
        Skip create if the same note+date+matter already exists.
        """
        return await provider.create_time_entry(
            date=date,
            matter_id=matter_id,
            note=note,
            hours=hours,
            quantity_seconds=quantity_seconds,
            user_id=user_id,
            custom_rate=custom_rate,
            flat_rate=flat_rate,
            price=price,
            non_billable=non_billable,
        )

    @mcp.tool(name="clio_update_time_entry")
    async def clio_update_time_entry(
        activity_id: int,
        hours: Optional[float] = None,
        quantity_seconds: Optional[int] = None,
        note: Optional[str] = None,
        date: Optional[str] = None,
        custom_rate: Optional[float] = None,
        flat_rate: Optional[bool] = None,
        price: Optional[float] = None,
        non_billable: Optional[bool] = None,
    ) -> dict[str, Any]:
        """PATCH a time entry. Billed entries cannot be changed (Clio returns 403).

        Same hours vs quantity_seconds rules as create. Do not create a second entry to 'fix' one.
        """
        return await provider.update_time_entry(
            activity_id=activity_id,
            hours=hours,
            quantity_seconds=quantity_seconds,
            note=note,
            date=date,
            custom_rate=custom_rate,
            flat_rate=flat_rate,
            price=price,
            non_billable=non_billable,
        )
