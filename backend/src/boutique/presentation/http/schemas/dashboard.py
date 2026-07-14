from datetime import date, datetime
from decimal import Decimal

from boutique.domain.dashboard.models import (
    CategoryRevenueConcentrationPoint,
    CohortRetentionPoint,
    DashboardSummary,
    DataFreshness,
    LogNormalFit,
    OrderValueDistributionBin,
    PearsonCorrelation,
    RevenuePoint,
)
from boutique.presentation.http.schemas.base import Schema


class DashboardSummaryResponseSchema(Schema):
    revenue: Decimal
    delivered_orders: int
    average_order_value: Decimal

    @classmethod
    def from_domain(cls, *, summary: DashboardSummary) -> "DashboardSummaryResponseSchema":
        return cls(
            revenue=summary.revenue.amount,
            delivered_orders=summary.delivered_orders,
            average_order_value=summary.average_order_value.amount,
        )


class RevenuePointResponseSchema(Schema):
    period: date
    revenue: Decimal
    order_count: int

    @classmethod
    def from_domain(cls, *, point: RevenuePoint) -> "RevenuePointResponseSchema":
        return cls(period=point.period, revenue=point.revenue.amount, order_count=point.order_count)


class RecentOrderResponseSchema(Schema):
    id: str
    customer_id: str
    status: str
    purchased_at: date
    total: Decimal


class OrderValueDistributionBinResponseSchema(Schema):
    lower_bound: Decimal
    upper_bound: Decimal
    order_count: int

    @classmethod
    def from_domain(
        cls,
        *,
        distribution_bin: OrderValueDistributionBin,
    ) -> "OrderValueDistributionBinResponseSchema":
        return cls(
            lower_bound=distribution_bin.lower_bound.amount,
            upper_bound=distribution_bin.upper_bound.amount,
            order_count=distribution_bin.order_count,
        )


class PearsonCorrelationResponseSchema(Schema):
    x: str
    y: str
    coefficient: float | None

    @classmethod
    def from_domain(cls, *, correlation: PearsonCorrelation) -> "PearsonCorrelationResponseSchema":
        return cls(
            x=correlation.x,
            y=correlation.y,
            coefficient=correlation.coefficient,
        )


class OrderValueDensityPointResponseSchema(Schema):
    order_value: Decimal
    density: float


class LogNormalQuantilePointResponseSchema(Schema):
    theoretical_value: Decimal
    observed_value: Decimal


class LogNormalFitResponseSchema(Schema):
    sample_size: int
    mu: float | None
    sigma: float | None
    log_likelihood: float | None
    aic: float | None
    bic: float | None
    density_points: list[OrderValueDensityPointResponseSchema]
    kde_points: list[OrderValueDensityPointResponseSchema]
    qq_points: list[LogNormalQuantilePointResponseSchema]

    @classmethod
    def from_domain(cls, *, fit: LogNormalFit) -> "LogNormalFitResponseSchema":
        return cls(
            sample_size=fit.sample_size,
            mu=fit.mu,
            sigma=fit.sigma,
            log_likelihood=fit.log_likelihood,
            aic=fit.aic,
            bic=fit.bic,
            density_points=[
                OrderValueDensityPointResponseSchema(
                    order_value=point.order_value.amount,
                    density=point.density,
                )
                for point in fit.density_points
            ],
            kde_points=[
                OrderValueDensityPointResponseSchema(
                    order_value=point.order_value.amount,
                    density=point.density,
                )
                for point in fit.kde_points
            ],
            qq_points=[
                LogNormalQuantilePointResponseSchema(
                    theoretical_value=point.theoretical_value.amount,
                    observed_value=point.observed_value.amount,
                )
                for point in fit.qq_points
            ],
        )


class CategoryRevenueConcentrationPointResponseSchema(Schema):
    category: str
    revenue: Decimal
    cumulative_share: float

    @classmethod
    def from_domain(
        cls,
        *,
        point: CategoryRevenueConcentrationPoint,
    ) -> "CategoryRevenueConcentrationPointResponseSchema":
        return cls(
            category=point.category,
            revenue=point.revenue.amount,
            cumulative_share=point.cumulative_share,
        )


class CohortRetentionPointResponseSchema(Schema):
    cohort_month: date
    active_customers: int
    month_number: int
    retention_rate: float

    @classmethod
    def from_domain(cls, *, point: CohortRetentionPoint) -> "CohortRetentionPointResponseSchema":
        return cls(
            cohort_month=point.cohort_month,
            active_customers=point.active_customers,
            month_number=point.month_number,
            retention_rate=point.retention_rate,
        )


class DataFreshnessResponseSchema(Schema):
    last_imported_at: datetime | None

    @classmethod
    def from_domain(cls, *, data_freshness: DataFreshness) -> "DataFreshnessResponseSchema":
        return cls(last_imported_at=data_freshness.last_imported_at)
