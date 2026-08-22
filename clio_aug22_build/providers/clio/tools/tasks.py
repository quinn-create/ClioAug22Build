from __future__ import annotations

from typing import Any, Literal, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_list_tasks")
    async def clio_list_tasks(
        matter_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """List tasks, optionally by matter, assignee, or status. ALWAYS list before creating.

        Prefer this over clio_api_request GET /tasks. Get your user id from clio_who_am_i
        if you need assignee_id = me.
        """
        return await provider.list_tasks(
            matter_id=matter_id,
            assignee_id=assignee_id,
            status=status,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_create_task")
    async def clio_create_task(
        name: str,
        matter_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        due_at: Optional[str] = None,
        priority: Optional[Literal["High", "Normal", "Low"]] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a task. ALWAYS clio_list_tasks on that matter first.

        Skip create if an open task with the same name already exists on the matter.
        due_at is ISO-8601. Default status is pending.
        """
        return await provider.create_task(
            name=name,
            matter_id=matter_id,
            assignee_id=assignee_id,
            due_at=due_at,
            priority=priority,
            description=description,
            status=status,
        )

    @mcp.tool(name="clio_update_task")
    async def clio_update_task(
        task_id: int,
        name: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[Literal["High", "Normal", "Low"]] = None,
        due_at: Optional[str] = None,
        assignee_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """PATCH an existing task (status, due date, assignee, name). Do not create a duplicate."""
        return await provider.update_task(
            task_id=task_id,
            name=name,
            status=status,
            priority=priority,
            due_at=due_at,
            assignee_id=assignee_id,
            description=description,
        )
