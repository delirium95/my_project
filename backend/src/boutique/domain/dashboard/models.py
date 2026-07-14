from datetime import date, datetime
from decimal import Decimal

from boutique.domain.common.models import ValueObject
from boutique.domain.common.value_objects import Money
from boutique.domain.ids import CustomerID, OrderID
from boutique.domain.orders.enums import OrderStatus


class DashboardSummary(ValueObject):
    revenue: Money
    delivered_orders: int
    average_order_value: Money

    def to_cache_payload(self) -> dict[str, str | int]:
        return {
            "revenue": str(self.revenue.amount),
            "delivered_orders": self.delivered_orders,
            "average_order_value": str(self.average_order_value.amount),
        }

    @classmethod
    def from_cache_payload(cls, *, payload: dict[str, str | int]) -> "DashboardSummary":
        return cls(
            revenue=Money(amount=Decimal(str(payload["revenue"]))),
            delivered_orders=int(payload["delivered_orders"]),
            average_order_value=Money(amount=Decimal(str(payload["average_order_value"]))),
        )


class RevenuePoint(ValueObject):
    period: date
    revenue: Money
    order_count: int

    def to_cache_payload(self) -> dict[str, str | int]:
        return {
            "period": self.period.isoformat(),
            "revenue": str(self.revenue.amount),
            "order_count": self.order_count,
        }

    @classmethod
    def from_cache_payload(cls, *, payload: dict[str, str | int]) -> "RevenuePoint":
        return cls(
            period=date.fromisoformat(str(payload["period"])),
            revenue=Money(amount=Decimal(str(payload["revenue"]))),
            order_count=int(payload["order_count"]),
        )


class RecentOrder(ValueObject):
    id: OrderID
    customer_id: CustomerID
    status: OrderStatus
    purchased_at: date
    total: Money


class OrderValueDistributionBin(ValueObject):
    lower_bound: Money
    upper_bound: Money
    order_count: int


class PearsonCorrelation(ValueObject):
    x: str
    y: str
    coefficient: float | None


class LogNormalDensityPoint(ValueObject):
    order_value: Money
    density: float


class LogNormalQuantilePoint(ValueObject):
    theoretical_value: Money
    observed_value: Money


class KernelDensityPoint(ValueObject):
    order_value: Money
    density: float


class LogNormalFit(ValueObject):
    sample_size: int
    mu: float | None
    sigma: float | None
    log_likelihood: float | None
    aic: float | None
    bic: float | None
    density_points: list[LogNormalDensityPoint]
    kde_points: list[KernelDensityPoint]
    qq_points: list[LogNormalQuantilePoint]


class CategoryRevenueConcentrationPoint(ValueObject):
    category: str
    revenue: Money
    cumulative_share: float


class CohortRetentionPoint(ValueObject):
    cohort_month: date
    active_customers: int
    month_number: int
    retention_rate: float


class DataFreshness(ValueObject):
    last_imported_at: datetime | None
