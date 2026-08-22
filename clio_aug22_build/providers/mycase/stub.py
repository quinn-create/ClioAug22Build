from __future__ import annotations

from typing import Any


class MycaseProvider:
    name = "mycase"

    async def close(self) -> None:
        return None

    async def health(self) -> dict[str, Any]:
        return {"ok": False, "provider": "mycase", "error": "not_implemented"}

    async def who_am_i(self) -> dict[str, Any]:
        return self._nyi()

    async def find_contacts(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def get_contact(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_person(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_company(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_contact(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def find_matters(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def get_matter(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_matter(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_matter(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def list_calendar_entries(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_calendar_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_calendar_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def list_tasks(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_task(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_task(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def list_activities(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_time_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_time_entry(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def list_notes(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def create_note(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def update_note(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def list_documents(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    async def raw_request(self, **kwargs: Any) -> dict[str, Any]:
        return self._nyi()

    def _nyi(self) -> dict[str, Any]:
        return {
            "ok": False,
            "status": 501,
            "error": "not_implemented",
            "message": "MyCase is not implemented in v1. Set PROVIDER=clio.",
            "hint": "See clio_aug22_build/providers/mycase/README.md",
        }
