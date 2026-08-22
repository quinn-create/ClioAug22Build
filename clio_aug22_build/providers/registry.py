from __future__ import annotations

from clio_aug22_build.config import Settings
from clio_aug22_build.providers.base import PracticeManagementProvider


def build_provider(settings: Settings) -> PracticeManagementProvider:
    if settings.provider == "mycase":
        from clio_aug22_build.providers.mycase.stub import MycaseProvider

        return MycaseProvider()
    from clio_aug22_build.providers.clio.provider import ClioProvider

    return ClioProvider.from_settings(settings)
