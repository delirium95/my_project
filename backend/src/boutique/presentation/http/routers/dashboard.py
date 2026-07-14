from datetime import date
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query

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
from boutique.presentation.http.schemas.dashboard import (
    CategoryRevenueConcentrationPointResponseSchema,
    CohortRetentionPointResponseSchema,
    DashboardSummaryResponseSchema,
    DataFreshnessResponseSchema,
    LogNormalFitResponseSchema,
    OrderValueDistributionBinResponseSchema,
    PearsonCorrelationResponseSchema,
    RecentOrderResponseSchema,
    RevenuePointResponseSchema,
)
from boutique.presentation.http.security import get_authenticated_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_authenticated_user)],
)


@router.get("/summary", response_model=DashboardSummaryResponseSchema)
@inject
async def get_dashboard_summary(
    use_case: Annotated[GetDashboardSummaryUseCase, Depends(Provide["get_dashboard_summary"])],
) -> DashboardSummaryResponseSchema:
    return DashboardSummaryResponseSchema.from_domain(summary=await use_case())


@router.get("/revenue", response_model=list[RevenuePointResponseSchema])
@inject
async def get_monthly_revenue(
    use_case: Annotated[GetMonthlyRevenueUseCase, Depends(Provide["get_monthly_revenue"])],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[RevenuePointResponseSchema]:
    _validate_date_range(start_date=start_date, end_date=end_date)
    points = await use_case(start_date=start_date, end_date=end_date)
    return [RevenuePointResponseSchema.from_domain(point=point) for point in points]


@router.get("/orders", response_model=list[RecentOrderResponseSchema])
@inject
async def list_recent_orders(
    use_case: Annotated[ListRecentOrdersUseCase, Depends(Provide["list_recent_orders"])],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[RecentOrderResponseSchema]:
    orders = await use_case(limit=limit)
    return [
        RecentOrderResponseSchema(
            id=order.id,
            customer_id=order.customer_id,
            status=order.status,
            purchased_at=order.purchased_at,
            total=order.total.amount,
        )
        for order in orders
    ]


@router.get("/distribution", response_model=list[OrderValueDistributionBinResponseSchema])
@inject
async def get_order_value_distribution(
    use_case: Annotated[
        GetOrderValueDistributionUseCase,
        Depends(Provide["get_order_value_distribution"]),
    ],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[OrderValueDistributionBinResponseSchema]:
    _validate_date_range(start_date=start_date, end_date=end_date)
    distribution = await use_case(start_date=start_date, end_date=end_date)
    return [
        OrderValueDistributionBinResponseSchema.from_domain(distribution_bin=distribution_bin)
        for distribution_bin in distribution
    ]


@router.get("/correlations", response_model=list[PearsonCorrelationResponseSchema])
@inject
async def get_pearson_correlations(
    use_case: Annotated[
        GetPearsonCorrelationsUseCase,
        Depends(Provide["get_pearson_correlations"]),
    ],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[PearsonCorrelationResponseSchema]:
    _validate_date_range(start_date=start_date, end_date=end_date)
    correlations = await use_case(start_date=start_date, end_date=end_date)
    return [
        PearsonCorrelationResponseSchema.from_domain(correlation=correlation)
        for correlation in correlations
    ]


@router.get("/fit/log-normal", response_model=LogNormalFitResponseSchema)
@inject
async def get_log_normal_fit(
    use_case: Annotated[GetLogNormalFitUseCase, Depends(Provide["get_log_normal_fit"])],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> LogNormalFitResponseSchema:
    _validate_date_range(start_date=start_date, end_date=end_date)
    return LogNormalFitResponseSchema.from_domain(
        fit=await use_case(start_date=start_date, end_date=end_date)
    )


@router.get("/pareto", response_model=list[CategoryRevenueConcentrationPointResponseSchema])
@inject
async def get_category_revenue_concentration(
    use_case: Annotated[
        GetCategoryRevenueConcentrationUseCase,
        Depends(Provide["get_category_revenue_concentration"]),
    ],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[CategoryRevenueConcentrationPointResponseSchema]:
    _validate_date_range(start_date=start_date, end_date=end_date)
    points = await use_case(start_date=start_date, end_date=end_date)
    return [
        CategoryRevenueConcentrationPointResponseSchema.from_domain(point=point) for point in points
    ]


@router.get("/cohorts", response_model=list[CohortRetentionPointResponseSchema])
@inject
async def get_cohort_retention(
    use_case: Annotated[GetCohortRetentionUseCase, Depends(Provide["get_cohort_retention"])],
) -> list[CohortRetentionPointResponseSchema]:
    points = await use_case()
    return [CohortRetentionPointResponseSchema.from_domain(point=point) for point in points]


@router.get("/data-freshness", response_model=DataFreshnessResponseSchema)
@inject
async def get_data_freshness(
    use_case: Annotated[GetDataFreshnessUseCase, Depends(Provide["get_data_freshness"])],
) -> DataFreshnessResponseSchema:
    return DataFreshnessResponseSchema.from_domain(data_freshness=await use_case())


def _validate_date_range(*, start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date",
        )
