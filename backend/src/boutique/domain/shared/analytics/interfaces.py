from abc import ABC, abstractmethod
from typing import Any

from boutique.domain.ids import AuthSubject
from boutique.domain.shared.analytics.enums import AnalyticsEvent


class BaseCaptureAnalyticsEventService(ABC):
    """Best-effort port for recording product events."""

    @abstractmethod
    async def capture(
        self,
        actor_id: AuthSubject,
        event: AnalyticsEvent,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Record a non-critical event without changing the main request result."""
