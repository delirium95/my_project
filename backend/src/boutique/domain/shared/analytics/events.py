from typing import Any, ClassVar

from pydantic import ConfigDict

from boutique.domain.common.models import ValueObject
from boutique.domain.shared.analytics.enums import AnalyticsEvent


class AnalyticsEventPayload(ValueObject):
    """Typed properties of one product event."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    event: ClassVar[AnalyticsEvent]

    def properties(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
