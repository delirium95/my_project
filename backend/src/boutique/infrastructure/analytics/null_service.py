from typing import Any

from boutique.domain.ids import AuthSubject
from boutique.domain.shared.analytics.enums import AnalyticsEvent
from boutique.domain.shared.analytics.interfaces import BaseCaptureAnalyticsEventService


class NullAnalyticsCaptureService(BaseCaptureAnalyticsEventService):
    """Safe default before a PostHog project key is configured."""

    async def capture(
        self,
        actor_id: AuthSubject,
        event: AnalyticsEvent,
        properties: dict[str, Any] | None = None,
    ) -> None:
        return None
