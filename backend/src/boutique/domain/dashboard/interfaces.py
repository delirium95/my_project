from abc import ABC, abstractmethod
from datetime import date

from boutique.domain.dashboard.models import (
    CategoryRevenueConcentrationPoint,
    CohortRetentionPoint,
    DashboardSummary,
    DataFreshness,
    LogNormalFit,
    OrderValueDistributionBin,
    PearsonCorrelation,
    RecentOrder,
    RevenuePoint,
)


class DashboardQueryService(ABC):
    """Read-model contract for aggregate SQL queries used by dashboard charts."""

    @abstractmethod
    async def get_summary(self) -> DashboardSummary:
        """Return cached-independent dashboard headline metrics."""

    @abstractmethod
    async def get_monthly_revenue(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[RevenuePoint]:
        """Return monthly delivered-order revenue for the inclusive date range."""

    @abstractmethod
    async def list_recent_orders(self, *, limit: int) -> list[RecentOrder]:
        """Return the newest orders for the dashboard table."""

    @abstractmethod
    async def get_order_value_distribution(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[OrderValueDistributionBin]:
        """Return a ten-bin distribution of delivered order totals."""

    @abstractmethod
    async def get_pearson_correlations(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[PearsonCorrelation]:
        """Return Pearson correlations between delivered order-level numeric features."""

    @abstractmethod
    async def get_log_normal_fit(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> LogNormalFit:
        """Return fit diagnostics for delivered order totals in the selected date range."""

    @abstractmethod
    async def get_category_revenue_concentration(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[CategoryRevenueConcentrationPoint]:
        """Return a Pareto-style category revenue concentration curve."""

    @abstractmethod
    async def get_cohort_retention(self) -> list[CohortRetentionPoint]:
        """Return up to twelve months of repeat-customer retention cohorts."""

    @abstractmethod
    async def get_data_freshness(self) -> DataFreshness:
        """Return when a complete Olist dataset was last successfully imported."""
