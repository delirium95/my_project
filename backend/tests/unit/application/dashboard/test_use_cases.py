from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from boutique.application.dashboard.use_cases import (
    GetDashboardSummaryUseCaseImpl,
    GetMonthlyRevenueUseCaseImpl,
)
from boutique.domain.common.cache import BaseCacheService
from boutique.domain.common.value_objects import Money
from boutique.domain.dashboard.interfaces import DashboardQueryService
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


class FakeDashboardQueryService(DashboardQueryService):
    def __init__(self) -> None:
        self.summary_calls = 0
        self.revenue_calls = 0

    async def get_summary(self) -> DashboardSummary:
        self.summary_calls += 1
        return DashboardSummary(
            revenue=Money(amount=Decimal("12.50")),
            delivered_orders=1,
            average_order_value=Money(amount=Decimal("12.50")),
        )

    async def get_monthly_revenue(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[RevenuePoint]:
        self.revenue_calls += 1
        return [
            RevenuePoint(
                period=date(2025, 1, 1),
                revenue=Money(amount=Decimal("12.50")),
                order_count=1,
            )
        ]

    async def list_recent_orders(self, *, limit: int) -> list[RecentOrder]:
        return []

    async def get_order_value_distribution(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[OrderValueDistributionBin]:
        return []

    async def get_pearson_correlations(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[PearsonCorrelation]:
        return []

    async def get_log_normal_fit(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> LogNormalFit:
        return LogNormalFit(
            sample_size=0,
            mu=None,
            sigma=None,
            log_likelihood=None,
            aic=None,
            bic=None,
            density_points=[],
            kde_points=[],
            qq_points=[],
        )

    async def get_category_revenue_concentration(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[CategoryRevenueConcentrationPoint]:
        return []

    async def get_cohort_retention(self) -> list[CohortRetentionPoint]:
        return []

    async def get_data_freshness(self) -> DataFreshness:
        return DataFreshness(last_imported_at=None)


class InMemoryCacheService(BaseCacheService):
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    async def get(self, *, key: str) -> dict[str, Any] | None:
        return self.values.get(key)

    async def set(self, *, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        self.values[key] = value

    async def invalidate_prefix(self, *, prefix: str) -> None:
        self.values = {
            key: value for key, value in self.values.items() if not key.startswith(prefix)
        }


@pytest.mark.unit
async def test_summary_use_case_uses_cache_aside() -> None:
    query_service = FakeDashboardQueryService()
    use_case = GetDashboardSummaryUseCaseImpl(
        query_service=query_service,
        cache=InMemoryCacheService(),
        cache_ttl_seconds=60,
    )

    first_result = await use_case()
    second_result = await use_case()

    assert first_result == second_result
    assert query_service.summary_calls == 1


@pytest.mark.unit
async def test_revenue_use_case_scopes_cache_by_date_range() -> None:
    query_service = FakeDashboardQueryService()
    use_case = GetMonthlyRevenueUseCaseImpl(
        query_service=query_service,
        cache=InMemoryCacheService(),
        cache_ttl_seconds=60,
    )

    await use_case(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
    await use_case(start_date=date(2025, 2, 1), end_date=date(2025, 2, 28))

    assert query_service.revenue_calls == 2
