from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Float, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boutique.domain.common.value_objects import Money
from boutique.domain.dashboard.interfaces import DashboardQueryService
from boutique.domain.dashboard.models import (
    DashboardSummary,
    OrderValueDistributionBin,
    PearsonCorrelation,
    RecentOrder,
    RevenuePoint,
)
from boutique.domain.ids import CustomerID, OrderID
from boutique.domain.orders.enums import OrderStatus
from boutique.infrastructure.database.models import Order, OrderItem


class SqlAlchemyDashboardQueryService(DashboardQueryService):
    """PostgreSQL read adapter for dashboard analytics."""

    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_summary(self) -> DashboardSummary:
        async with self._session_factory() as session:
            result = await session.execute(
                select(
                    func.coalesce(func.sum(OrderItem.price + OrderItem.freight_value), 0).label(
                        "revenue"
                    ),
                    func.count(distinct(Order.id)).label("delivered_orders"),
                )
                .select_from(Order)
                .join(OrderItem, OrderItem.order_id == Order.id)
                .where(Order.status == "delivered")
            )
            revenue, delivered_orders = result.one()

        total_revenue = Money(amount=Decimal(revenue))
        order_count = int(delivered_orders)
        average_order_value = (
            total_revenue.divide(divisor=order_count) if order_count else Money.zero()
        )
        return DashboardSummary(
            revenue=total_revenue,
            delivered_orders=order_count,
            average_order_value=average_order_value,
        )

    async def get_monthly_revenue(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[RevenuePoint]:
        month = func.date_trunc("month", Order.purchased_at).label("month")
        statement = (
            select(
                month,
                func.coalesce(func.sum(OrderItem.price + OrderItem.freight_value), 0).label(
                    "revenue"
                ),
                func.count(distinct(Order.id)).label("order_count"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status == "delivered")
            .group_by(month)
            .order_by(month)
        )
        if start_date is not None:
            statement = statement.where(
                Order.purchased_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
            )
        if end_date is not None:
            exclusive_end = datetime.combine(
                end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC
            )
            statement = statement.where(Order.purchased_at < exclusive_end)

        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()

        return [
            RevenuePoint(
                period=row.month.date(),
                revenue=Money(amount=Decimal(row.revenue)),
                order_count=int(row.order_count),
            )
            for row in rows
        ]

    async def list_recent_orders(self, *, limit: int) -> list[RecentOrder]:
        statement = (
            select(
                Order.id,
                Order.customer_id,
                Order.status,
                Order.purchased_at,
                func.coalesce(func.sum(OrderItem.price + OrderItem.freight_value), 0).label(
                    "total"
                ),
            )
            .select_from(Order)
            .outerjoin(OrderItem, OrderItem.order_id == Order.id)
            .group_by(Order.id)
            .order_by(Order.purchased_at.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        return [
            RecentOrder(
                id=OrderID(row.id),
                customer_id=CustomerID(row.customer_id),
                status=OrderStatus(row.status),
                purchased_at=row.purchased_at.date(),
                total=Money(amount=Decimal(row.total)),
            )
            for row in rows
        ]

    async def get_order_value_distribution(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[OrderValueDistributionBin]:
        order_totals = self._delivered_order_totals(
            start_date=start_date,
            end_date=end_date,
        )
        async with self._session_factory() as session:
            minimum, maximum = (
                await session.execute(
                    select(func.min(order_totals.c.total), func.max(order_totals.c.total))
                )
            ).one()
            if minimum is None or maximum is None:
                return []

            minimum_total = Decimal(minimum)
            maximum_total = Decimal(maximum)
            order_count = int(
                await session.scalar(select(func.count()).select_from(order_totals)) or 0
            )
            if minimum_total == maximum_total:
                return [
                    OrderValueDistributionBin(
                        lower_bound=Money(amount=minimum_total),
                        upper_bound=Money(amount=maximum_total),
                        order_count=order_count,
                    )
                ]

            bucket_count = 10
            bucket = func.least(
                func.width_bucket(order_totals.c.total, minimum_total, maximum_total, bucket_count),
                bucket_count,
            ).label("bucket")
            rows = (
                await session.execute(
                    select(bucket, func.count().label("order_count"))
                    .select_from(order_totals)
                    .group_by(bucket)
                    .order_by(bucket)
                )
            ).all()

        counts = {int(row.bucket): int(row.order_count) for row in rows}
        bucket_width = (maximum_total - minimum_total) / bucket_count
        return [
            OrderValueDistributionBin(
                lower_bound=Money(amount=minimum_total + bucket_width * (index - 1)),
                upper_bound=Money(
                    amount=maximum_total
                    if index == bucket_count
                    else minimum_total + bucket_width * index
                ),
                order_count=counts.get(index, 0),
            )
            for index in range(1, bucket_count + 1)
        ]

    async def get_pearson_correlations(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[PearsonCorrelation]:
        order_totals = self._delivered_order_totals(
            start_date=start_date,
            end_date=end_date,
        )
        metrics = (
            ("Items", order_totals.c.item_count),
            ("Item value", order_totals.c.item_value),
            ("Freight", order_totals.c.freight),
            ("Order total", order_totals.c.total),
        )
        expressions = [
            func.corr(x_value.cast(Float), y_value.cast(Float)).label(f"correlation_{x}_{y}")
            for x, (_, x_value) in enumerate(metrics)
            for y, (_, y_value) in enumerate(metrics)
        ]
        async with self._session_factory() as session:
            row = (await session.execute(select(*expressions))).one()

        correlations: list[PearsonCorrelation] = []
        for x_index, (x_name, _) in enumerate(metrics):
            for y_index, (y_name, _) in enumerate(metrics):
                index = x_index * len(metrics) + y_index
                correlations.append(
                    PearsonCorrelation(
                        x=x_name,
                        y=y_name,
                        coefficient=float(row[index]) if row[index] is not None else None,
                    )
                )
        return correlations

    @staticmethod
    def _delivered_order_totals(*, start_date: date | None, end_date: date | None):
        statement = (
            select(
                Order.id.label("order_id"),
                func.count(OrderItem.id).label("item_count"),
                func.sum(OrderItem.price).label("item_value"),
                func.sum(OrderItem.freight_value).label("freight"),
                func.sum(OrderItem.price + OrderItem.freight_value).label("total"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .where(Order.status == "delivered")
            .group_by(Order.id)
        )
        if start_date is not None:
            statement = statement.where(
                Order.purchased_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=UTC)
            )
        if end_date is not None:
            exclusive_end = datetime.combine(
                end_date + timedelta(days=1), datetime.min.time(), tzinfo=UTC
            )
            statement = statement.where(Order.purchased_at < exclusive_end)
        return statement.subquery("delivered_order_totals")
