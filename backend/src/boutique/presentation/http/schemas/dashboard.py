from datetime import date
from decimal import Decimal

from boutique.domain.dashboard.models import (
    DashboardSummary,
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
