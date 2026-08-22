from __future__ import annotations

from typing import Any, Literal, Optional

from clio_aug22_build.providers.base import PracticeManagementProvider


def register(mcp: Any, provider: PracticeManagementProvider) -> None:
    @mcp.tool(name="clio_find_contacts")
    async def clio_find_contacts(
        query: Optional[str] = None,
        contact_type: Optional[Literal["Person", "Company"]] = None,
        limit: int = 25,
        page_token: Optional[str] = None,
        fields: Optional[str] = None,
        auto_page: bool = False,
    ) -> dict[str, Any]:
        """Search Clio contacts. ALWAYS call this before clio_create_person or clio_create_company.

        Use query for a name/email search (e.g. "Jane Doe"). Filter with contact_type
        Person or Company. If a close match exists, use that id — do not create a duplicate.
        Prefer this over clio_api_request GET /contacts.
        """
        return await provider.find_contacts(
            query=query,
            contact_type=contact_type,
            limit=min(max(limit, 1), 200),
            page_token=page_token,
            fields=fields,
            auto_page=auto_page,
        )

    @mcp.tool(name="clio_get_contact")
    async def clio_get_contact(
        contact_id: int,
        fields: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get one contact by id. Use when you already have the Clio contact id."""
        return await provider.get_contact(contact_id=contact_id, fields=fields)

    @mcp.tool(name="clio_create_person")
    async def clio_create_person(
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
        company_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a Person contact. NEVER call this until clio_find_contacts returned no match.

        Email/phone are simple strings; the server wraps them in Clio's address arrays.
        If find returned a same-name + email hit, return that existing id instead of creating.
        """
        return await provider.create_person(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            title=title,
            company_id=company_id,
            notes=notes,
        )

    @mcp.tool(name="clio_create_company")
    async def clio_create_company(
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
    ) -> dict[str, Any]:
        """Create a Company contact. ALWAYS clio_find_contacts(contact_type='Company') first.

        Use this for business clients. Do not jam a company through clio_create_person.
        """
        return await provider.create_company(
            name=name, email=email, phone=phone, website=website
        )

    @mcp.tool(name="clio_update_contact")
    async def clio_update_contact(
        contact_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        title: Optional[str] = None,
    ) -> dict[str, Any]:
        """PATCH an existing person or company. Never create a new contact to 'fix' one."""
        return await provider.update_contact(
            contact_id=contact_id,
            first_name=first_name,
            last_name=last_name,
            name=name,
            email=email,
            phone=phone,
            title=title,
        )
