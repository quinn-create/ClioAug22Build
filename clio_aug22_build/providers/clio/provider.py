from __future__ import annotations

from typing import Any

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.clio.client import ClioApiError, ClioClient
from clio_aug22_build.providers.clio.constants import DEFAULT_FIELDS, DOCUMENT_UPLOAD_GUIDANCE
from clio_aug22_build.providers.clio.util import drop_none, fail, nest_id, resolve_quantity_seconds


class ClioProvider:
    name = "clio"

    def __init__(self, client: ClioClient) -> None:
        self.client = client

    @classmethod
    def from_settings(cls, settings: Settings) -> "ClioProvider":
        return cls(ClioClient(settings))

    async def close(self) -> None:
        await self.client.close()

    async def health(self) -> dict[str, Any]:
        probe = await self.client.tokens.probe()
        return {"provider": self.name, **probe}

    async def who_am_i(self) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/users/who_am_i",
            default_fields=DEFAULT_FIELDS["who_am_i"],
        )

    async def find_contacts(
        self,
        query: str | None = None,
        contact_type: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/contacts",
            query={
                "query": query,
                "type": contact_type,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["contacts"],
            auto_page=auto_page,
        )

    async def get_contact(self, contact_id: int, fields: str | None = None) -> dict[str, Any]:
        return await self._call(
            "GET",
            f"/contacts/{contact_id}",
            query={"fields": fields},
            default_fields=DEFAULT_FIELDS["contacts"],
        )

    async def create_person(
        self,
        first_name: str,
        last_name: str,
        email: str | None = None,
        phone: str | None = None,
        title: str | None = None,
        company_id: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": "Person",
            "first_name": first_name,
            "last_name": last_name,
        }
        if title:
            body["title"] = title
        if email:
            body["email_addresses"] = [
                {"name": "Work", "address": email, "default_email": True}
            ]
        if phone:
            body["phone_numbers"] = [
                {"name": "Work", "number": phone, "default_number": True}
            ]
        if company_id:
            body["company"] = nest_id(company_id)
        return await self._call(
            "POST",
            "/contacts",
            query={"fields": DEFAULT_FIELDS["contacts"]},
            body=drop_none(body),
        )

    async def create_company(
        self,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        website: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"type": "Company", "name": name}
        if website:
            body["web_sites"] = [{"name": "Work", "address": website, "default_web_site": True}]
        if email:
            body["email_addresses"] = [
                {"name": "Work", "address": email, "default_email": True}
            ]
        if phone:
            body["phone_numbers"] = [
                {"name": "Work", "number": phone, "default_number": True}
            ]
        return await self._call(
            "POST",
            "/contacts",
            query={"fields": DEFAULT_FIELDS["contacts"]},
            body=body,
        )

    async def update_contact(
        self,
        contact_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = drop_none(
            {
                "first_name": first_name,
                "last_name": last_name,
                "name": name,
                "title": title,
            }
        )
        if email:
            body["email_addresses"] = [
                {"name": "Work", "address": email, "default_email": True}
            ]
        if phone:
            body["phone_numbers"] = [
                {"name": "Work", "number": phone, "default_number": True}
            ]
        if not body:
            return fail(400, "empty_update", "No fields to update", "Pass at least one field")
        return await self._call(
            "PATCH",
            f"/contacts/{contact_id}",
            query={"fields": DEFAULT_FIELDS["contacts"]},
            body=body,
        )

    async def find_matters(
        self,
        query: str | None = None,
        client_id: int | None = None,
        status: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/matters",
            query={
                "query": query,
                "client_id": client_id,
                "status": status,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["matters"],
            auto_page=auto_page,
        )

    async def get_matter(self, matter_id: int, fields: str | None = None) -> dict[str, Any]:
        return await self._call(
            "GET",
            f"/matters/{matter_id}",
            query={"fields": fields},
            default_fields=DEFAULT_FIELDS["matters"],
        )

    async def create_matter(
        self,
        client_id: int,
        description: str,
        status: str = "Open",
        open_date: str | None = None,
        practice_area_id: int | None = None,
        responsible_attorney_id: int | None = None,
        billable: bool = True,
    ) -> dict[str, Any]:
        body: dict[str, Any] = drop_none(
            {
                "client": nest_id(client_id),
                "description": description,
                "status": status,
                "open_date": open_date,
                "billable": billable,
                "practice_area": nest_id(practice_area_id),
                "responsible_attorney": nest_id(responsible_attorney_id),
            }
        )
        return await self._call(
            "POST",
            "/matters",
            query={"fields": DEFAULT_FIELDS["matters"]},
            body=body,
        )

    async def update_matter(
        self,
        matter_id: int,
        description: str | None = None,
        status: str | None = None,
        close_date: str | None = None,
        responsible_attorney_id: int | None = None,
        billable: bool | None = None,
        practice_area_id: int | None = None,
    ) -> dict[str, Any]:
        body = drop_none(
            {
                "description": description,
                "status": status,
                "close_date": close_date,
                "billable": billable,
                "responsible_attorney": nest_id(responsible_attorney_id),
                "practice_area": nest_id(practice_area_id),
            }
        )
        if not body:
            return fail(400, "empty_update", "No fields to update")
        return await self._call(
            "PATCH",
            f"/matters/{matter_id}",
            query={"fields": DEFAULT_FIELDS["matters"]},
            body=body,
        )

    async def list_calendar_entries(
        self,
        from_datetime: str,
        to_datetime: str,
        matter_id: int | None = None,
        query: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/calendar_entries",
            query={
                "from": from_datetime,
                "to": to_datetime,
                "matter_id": matter_id,
                "query": query,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["calendar_entries"],
            auto_page=auto_page,
        )

    async def create_calendar_entry(
        self,
        summary: str,
        start_at: str,
        end_at: str,
        all_day: bool = False,
        description: str | None = None,
        location: str | None = None,
        matter_id: int | None = None,
        attendee_user_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = drop_none(
            {
                "summary": summary,
                "start_at": start_at,
                "end_at": end_at,
                "all_day": all_day,
                "description": description,
                "location": location,
                "matter": nest_id(matter_id),
            }
        )
        if attendee_user_ids:
            body["attendees"] = [{"id": int(i), "type": "User"} for i in attendee_user_ids]
        return await self._call(
            "POST",
            "/calendar_entries",
            query={"fields": DEFAULT_FIELDS["calendar_entries"]},
            body=body,
        )

    async def update_calendar_entry(
        self,
        entry_id: int,
        summary: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
        all_day: bool | None = None,
        description: str | None = None,
        location: str | None = None,
        matter_id: int | None = None,
    ) -> dict[str, Any]:
        body = drop_none(
            {
                "summary": summary,
                "start_at": start_at,
                "end_at": end_at,
                "all_day": all_day,
                "description": description,
                "location": location,
                "matter": nest_id(matter_id),
            }
        )
        if not body:
            return fail(400, "empty_update", "No fields to update")
        return await self._call(
            "PATCH",
            f"/calendar_entries/{entry_id}",
            query={"fields": DEFAULT_FIELDS["calendar_entries"]},
            body=body,
        )

    async def list_tasks(
        self,
        matter_id: int | None = None,
        assignee_id: int | None = None,
        status: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/tasks",
            query={
                "matter_id": matter_id,
                "assignee_id": assignee_id,
                "status": status,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["tasks"],
            auto_page=auto_page,
        )

    async def create_task(
        self,
        name: str,
        matter_id: int | None = None,
        assignee_id: int | None = None,
        due_at: str | None = None,
        priority: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        body = drop_none(
            {
                "name": name,
                "status": status or "pending",
                "priority": priority,
                "due_at": due_at,
                "description": description,
                "matter": nest_id(matter_id),
                "assignee": nest_id(assignee_id),
            }
        )
        return await self._call(
            "POST",
            "/tasks",
            query={"fields": DEFAULT_FIELDS["tasks"]},
            body=body,
        )

    async def update_task(
        self,
        task_id: int,
        name: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        due_at: str | None = None,
        assignee_id: int | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        body = drop_none(
            {
                "name": name,
                "status": status,
                "priority": priority,
                "due_at": due_at,
                "description": description,
                "assignee": nest_id(assignee_id),
            }
        )
        if not body:
            return fail(400, "empty_update", "No fields to update")
        return await self._call(
            "PATCH",
            f"/tasks/{task_id}",
            query={"fields": DEFAULT_FIELDS["tasks"]},
            body=body,
        )

    async def list_activities(
        self,
        matter_id: int | None = None,
        user_id: int | None = None,
        activity_type: str | None = "TimeEntry",
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        result = await self._call(
            "GET",
            "/activities",
            query={
                "matter_id": matter_id,
                "user_id": user_id,
                "type": activity_type,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["activities"],
            auto_page=auto_page,
        )
        if result.get("ok") and (date_from or date_to) and isinstance(result.get("data"), list):
            filtered = []
            for row in result["data"]:
                day = (row or {}).get("date") or ""
                if date_from and day < date_from:
                    continue
                if date_to and day > date_to:
                    continue
                filtered.append(row)
            result["data"] = filtered
            result["warning"] = (
                (result.get("warning") + " | ") if result.get("warning") else ""
            ) + "date_from/date_to filtered this page in-memory (Clio has no first-class date range on activities)"
        return result

    async def create_time_entry(
        self,
        date: str,
        matter_id: int,
        note: str,
        hours: float | None = None,
        quantity_seconds: int | None = None,
        user_id: int | None = None,
        custom_rate: float | None = None,
        flat_rate: bool | None = None,
        price: float | None = None,
        non_billable: bool | None = None,
    ) -> dict[str, Any]:
        try:
            quantity = resolve_quantity_seconds(hours, quantity_seconds)
        except ValueError as exc:
            return fail(400, "missing_quantity", str(exc), "Pass hours (e.g. 0.3) or quantity_seconds")
        body = drop_none(
            {
                "type": "TimeEntry",
                "date": date,
                "quantity": quantity,
                "note": note,
                "matter": nest_id(matter_id),
                "user": nest_id(user_id),
                "custom_rate": custom_rate,
                "flat_rate": flat_rate,
                "price": price,
                "non_billable": non_billable,
            }
        )
        return await self._call(
            "POST",
            "/activities",
            query={"fields": DEFAULT_FIELDS["activities"]},
            body=body,
        )

    async def update_time_entry(
        self,
        activity_id: int,
        hours: float | None = None,
        quantity_seconds: int | None = None,
        note: str | None = None,
        date: str | None = None,
        custom_rate: float | None = None,
        flat_rate: bool | None = None,
        price: float | None = None,
        non_billable: bool | None = None,
    ) -> dict[str, Any]:
        body = drop_none(
            {
                "note": note,
                "date": date,
                "custom_rate": custom_rate,
                "flat_rate": flat_rate,
                "price": price,
                "non_billable": non_billable,
            }
        )
        if hours is not None or quantity_seconds is not None:
            try:
                body["quantity"] = resolve_quantity_seconds(hours, quantity_seconds)
            except ValueError as exc:
                return fail(400, "missing_quantity", str(exc))
        if not body:
            return fail(400, "empty_update", "No fields to update")
        return await self._call(
            "PATCH",
            f"/activities/{activity_id}",
            query={"fields": DEFAULT_FIELDS["activities"]},
            body=body,
        )

    async def list_notes(
        self,
        note_type: str,
        matter_id: int | None = None,
        contact_id: int | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        return await self._call(
            "GET",
            "/notes",
            query={
                "type": note_type,
                "matter_id": matter_id,
                "contact_id": contact_id,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["notes"],
            auto_page=auto_page,
        )

    async def create_note(
        self,
        note_type: str,
        detail: str,
        matter_id: int | None = None,
        contact_id: int | None = None,
        subject: str | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        if note_type == "Matter" and not matter_id:
            return fail(400, "missing_matter", "Matter notes require matter_id")
        if note_type == "Contact" and not contact_id:
            return fail(400, "missing_contact", "Contact notes require contact_id")
        body = drop_none(
            {
                "type": note_type,
                "detail": detail,
                "subject": subject,
                "date": date,
                "matter": nest_id(matter_id),
                "contact": nest_id(contact_id),
            }
        )
        return await self._call(
            "POST",
            "/notes",
            query={"fields": DEFAULT_FIELDS["notes"]},
            body=body,
        )

    async def update_note(
        self,
        note_id: int,
        detail: str | None = None,
        subject: str | None = None,
        date: str | None = None,
    ) -> dict[str, Any]:
        body = drop_none({"detail": detail, "subject": subject, "date": date})
        if not body:
            return fail(400, "empty_update", "No fields to update")
        return await self._call(
            "PATCH",
            f"/notes/{note_id}",
            query={"fields": DEFAULT_FIELDS["notes"]},
            body=body,
        )

    async def list_documents(
        self,
        matter_id: int | None = None,
        query: str | None = None,
        limit: int = 25,
        page_token: str | None = None,
        fields: str | None = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        result = await self._call(
            "GET",
            "/documents",
            query={
                "matter_id": matter_id,
                "query": query,
                "limit": limit,
                "page_token": page_token,
                "fields": fields,
                "order": "id(asc)",
            },
            default_fields=DEFAULT_FIELDS["documents"],
            auto_page=auto_page,
        )
        if result.get("ok"):
            result["upload_guidance"] = DOCUMENT_UPLOAD_GUIDANCE
        return result

    async def raw_request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: Any = None,
        raw: bool = False,
        auto_page: bool = False,
        max_pages: int = 5,
    ) -> dict[str, Any]:
        result = await self._call(
            method,
            path,
            query=query,
            body=body,
            raw=raw,
            auto_page=auto_page,
            max_pages=max_pages,
        )
        if result.get("ok") and not raw and method.upper() in {"POST", "PATCH", "PUT"}:
            result["envelope"] = (
                "Body was auto-wrapped in {\"data\": ...} because raw=false. "
                "Pass raw=true to send the body exactly as given."
            )
        if result.get("ok") and raw and method.upper() in {"POST", "PATCH", "PUT"}:
            result["envelope"] = "raw=true: body sent exactly as given, no {data: ...} wrap."
        return result

    async def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            return await self.client.request(method, path, **kwargs)
        except ClioApiError as exc:
            return exc.as_dict()
