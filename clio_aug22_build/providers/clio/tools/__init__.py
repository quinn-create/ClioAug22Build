from __future__ import annotations

from typing import Any

from clio_aug22_build.providers.base import PracticeManagementProvider


def register_clio_tools(mcp: Any, provider: PracticeManagementProvider) -> None:
    from clio_aug22_build.providers.clio.tools.activities import register as reg_activities
    from clio_aug22_build.providers.clio.tools.calendar import register as reg_calendar
    from clio_aug22_build.providers.clio.tools.contacts import register as reg_contacts
    from clio_aug22_build.providers.clio.tools.documents import register as reg_documents
    from clio_aug22_build.providers.clio.tools.generic import register as reg_generic
    from clio_aug22_build.providers.clio.tools.matters import register as reg_matters
    from clio_aug22_build.providers.clio.tools.notes import register as reg_notes
    from clio_aug22_build.providers.clio.tools.tasks import register as reg_tasks
    from clio_aug22_build.providers.clio.tools.whoami import register as reg_whoami

    reg_whoami(mcp, provider)
    reg_contacts(mcp, provider)
    reg_matters(mcp, provider)
    reg_calendar(mcp, provider)
    reg_tasks(mcp, provider)
    reg_activities(mcp, provider)
    reg_notes(mcp, provider)
    reg_documents(mcp, provider)
    reg_generic(mcp, provider)
