from datetime import date

from boutique.application.dashboard.cache_keys import (
    dashboard_summary_cache_key,
    monthly_revenue_cache_key,
)
from boutique.application.dashboard.interfaces import (
    GetCategoryRevenueConcentrationUseCase,
    GetCohortRetentionUseCase,
    GetDashboardSummaryUseCase,
    GetDataFreshnessUseCase,
    GetLogNormalFitUseCase,
    GetMonthlyRevenueUseCase,
    GetOrderValueDistributionUseCase,
    GetPearsonCorrelationsUseCase,
    ListRecentOrdersUseCase,
)
from boutique.domain.common.cache import BaseCacheService
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


class GetDashboardSummaryUseCaseImpl(GetDashboardSummaryUseCase):
    def __init__(
        self,
        *,
        query_service: DashboardQueryService,
        cache: BaseCacheService,
        cache_ttl_seconds: int,
    ) -> None:
        self._query_service = query_service
        self._cache = cache
        self._cache_ttl_seconds = cache_ttl_seconds

    async def __call__(self) -> DashboardSummary:
        cache_key = dashboard_summary_cache_key()
        payload = await self._cache.get(key=cache_key)
        if payload is not None:
            return DashboardSummary.from_cache_payload(payload=payload)

        summary = await self._query_service.get_summary()
        await self._cache.set(
            key=cache_key,
            value=summary.to_cache_payload(),
            ttl_seconds=self._cache_ttl_seconds,
        )
        return summary


class GetMonthlyRevenueUseCaseImpl(GetMonthlyRevenueUseCase):
    def __init__(
        self,
        *,
        query_service: DashboardQueryService,
        cache: BaseCacheService,
        cache_ttl_seconds: int,
    ) -> None:
        self._query_service = query_service
        self._cache = cache
        self._cache_ttl_seconds = cache_ttl_seconds

    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[RevenuePoint]:
        key = monthly_revenue_cache_key(start_date=start_date, end_date=end_date)
        payload = await self._cache.get(key=key)
        if payload is not None:
            points = payload.get("points", [])
            return [RevenuePoint.from_cache_payload(payload=point) for point in points]

        points = await self._query_service.get_monthly_revenue(
            start_date=start_date,
            end_date=end_date,
        )
        await self._cache.set(
            key=key,
            value={"points": [point.to_cache_payload() for point in points]},
            ttl_seconds=self._cache_ttl_seconds,
        )
        return points


class ListRecentOrdersUseCaseImpl(ListRecentOrdersUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(self, *, limit: int) -> list[RecentOrder]:
        return await self._query_service.list_recent_orders(limit=limit)


class GetOrderValueDistributionUseCaseImpl(GetOrderValueDistributionUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[OrderValueDistributionBin]:
        return await self._query_service.get_order_value_distribution(
            start_date=start_date,
            end_date=end_date,
        )


class GetPearsonCorrelationsUseCaseImpl(GetPearsonCorrelationsUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[PearsonCorrelation]:
        return await self._query_service.get_pearson_correlations(
            start_date=start_date,
            end_date=end_date,
        )


class GetLogNormalFitUseCaseImpl(GetLogNormalFitUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> LogNormalFit:
        return await self._query_service.get_log_normal_fit(
            start_date=start_date,
            end_date=end_date,
        )


class GetCategoryRevenueConcentrationUseCaseImpl(GetCategoryRevenueConcentrationUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[CategoryRevenueConcentrationPoint]:
        return await self._query_service.get_category_revenue_concentration(
            start_date=start_date,
            end_date=end_date,
        )


class GetCohortRetentionUseCaseImpl(GetCohortRetentionUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(self) -> list[CohortRetentionPoint]:
        return await self._query_service.get_cohort_retention()


class GetDataFreshnessUseCaseImpl(GetDataFreshnessUseCase):
    def __init__(self, *, query_service: DashboardQueryService) -> None:
        self._query_service = query_service

    async def __call__(self) -> DataFreshness:
        return await self._query_service.get_data_freshness()
