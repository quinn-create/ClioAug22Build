from __future__ import annotations

from typing import Any, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_list_documents")
    async def clio_list_documents(
        matter_id: Optional[int] = None,
        query: Optional[str] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """List document metadata on a matter (name, size, type, latest version).

        v1 does NOT upload binary files. The result includes upload_guidance for Clio's
        3-step flow: POST metadata via clio_api_request, PUT bytes to put_url, mark uploaded.
        ALWAYS list before creating metadata so you do not duplicate a filename.
        """
        return await provider.list_documents(
            matter_id=matter_id,
            query=query,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )
