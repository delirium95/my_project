from abc import ABC, abstractmethod
from datetime import date

from boutique.domain.dashboard.models import (
    DashboardSummary,
    OrderValueDistributionBin,
    PearsonCorrelation,
    RecentOrder,
    RevenuePoint,
)


class GetDashboardSummaryUseCase(ABC):
    @abstractmethod
    async def __call__(self) -> DashboardSummary:
        """Return the dashboard summary."""


class GetMonthlyRevenueUseCase(ABC):
    @abstractmethod
    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[RevenuePoint]:
        """Return monthly revenue for the selected inclusive date range."""


class ListRecentOrdersUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, limit: int) -> list[RecentOrder]:
        """Return the most recent orders for the dashboard table."""


class GetOrderValueDistributionUseCase(ABC):
    @abstractmethod
    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[OrderValueDistributionBin]:
        """Return the delivered-order value histogram for the selected date range."""


class GetPearsonCorrelationsUseCase(ABC):
    @abstractmethod
    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[PearsonCorrelation]:
        """Return the delivered-order Pearson correlation matrix for the selected date range."""
