import math
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from statistics import NormalDist

from sqlalchemy import Float, Integer, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boutique.domain.common.value_objects import Money
from boutique.domain.dashboard.interfaces import DashboardQueryService
from boutique.domain.dashboard.models import (
    CategoryRevenueConcentrationPoint,
    CohortRetentionPoint,
    DashboardSummary,
    DataFreshness,
    KernelDensityPoint,
    LogNormalDensityPoint,
    LogNormalFit,
    LogNormalQuantilePoint,
    OrderValueDistributionBin,
    PearsonCorrelation,
    RecentOrder,
    RevenuePoint,
)
from boutique.domain.ids import CustomerID, OrderID
from boutique.domain.orders.enums import OrderStatus
from boutique.infrastructure.database.models import (
    Customer,
    DatasetMetadata,
    Order,
    OrderItem,
    Product,
)


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

    async def get_log_normal_fit(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> LogNormalFit:
        order_totals = self._delivered_order_totals(
            start_date=start_date,
            end_date=end_date,
        )
        async with self._session_factory() as session:
            totals = (
                await session.scalars(
                    select(order_totals.c.total)
                    .where(order_totals.c.total > 0)
                    .order_by(order_totals.c.total)
                )
            ).all()
        return _build_log_normal_fit(values=[float(total) for total in totals])

    async def get_category_revenue_concentration(
        self,
        *,
        start_date: date | None,
        end_date: date | None,
    ) -> list[CategoryRevenueConcentrationPoint]:
        category = func.coalesce(Product.category, "Uncategorized").label("category")
        statement = (
            select(
                category,
                func.sum(OrderItem.price + OrderItem.freight_value).label("revenue"),
            )
            .select_from(Order)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Order.status == "delivered")
            .group_by(category)
            .order_by(func.sum(OrderItem.price + OrderItem.freight_value).desc())
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
        if not rows:
            return []

        category_revenues = [(str(row.category), Decimal(row.revenue)) for row in rows]
        visible_categories = category_revenues[:11]
        other_revenue = sum((revenue for _, revenue in category_revenues[11:]), Decimal(0))
        if other_revenue:
            visible_categories.append(("Other categories", other_revenue))
        total_revenue = sum((revenue for _, revenue in category_revenues), Decimal(0))
        cumulative_revenue = Decimal(0)
        points: list[CategoryRevenueConcentrationPoint] = []
        for category_name, revenue in visible_categories:
            cumulative_revenue += revenue
            points.append(
                CategoryRevenueConcentrationPoint(
                    category=category_name,
                    revenue=Money(amount=revenue),
                    cumulative_share=float(cumulative_revenue / total_revenue),
                )
            )
        return points

    async def get_cohort_retention(self) -> list[CohortRetentionPoint]:
        cohort_month = func.date_trunc("month", func.min(Order.purchased_at)).label("cohort_month")
        customer_cohorts = (
            select(
                Customer.unique_id.label("customer_unique_id"),
                cohort_month,
            )
            .select_from(Customer)
            .join(Order, Order.customer_id == Customer.id)
            .where(Order.status == "delivered")
            .group_by(Customer.unique_id)
            .subquery("customer_cohorts")
        )
        activity_month = func.date_trunc("month", Order.purchased_at)
        month_number = (
            (
                (
                    func.extract("year", activity_month)
                    - func.extract("year", customer_cohorts.c.cohort_month)
                )
                * 12
                + func.extract("month", activity_month)
                - func.extract("month", customer_cohorts.c.cohort_month)
            )
            .cast(Integer)
            .label("month_number")
        )
        statement = (
            select(
                customer_cohorts.c.cohort_month,
                month_number,
                func.count(distinct(customer_cohorts.c.customer_unique_id)).label(
                    "active_customers"
                ),
            )
            .select_from(customer_cohorts)
            .join(Customer, Customer.unique_id == customer_cohorts.c.customer_unique_id)
            .join(Order, Order.customer_id == Customer.id)
            .where(Order.status == "delivered")
            .group_by(customer_cohorts.c.cohort_month, month_number)
            .order_by(customer_cohorts.c.cohort_month, month_number)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()

        cohort_sizes = {
            row.cohort_month.date(): int(row.active_customers)
            for row in rows
            if int(row.month_number) == 0
        }
        return [
            CohortRetentionPoint(
                cohort_month=row.cohort_month.date(),
                active_customers=int(row.active_customers),
                month_number=int(row.month_number),
                retention_rate=int(row.active_customers) / cohort_sizes[row.cohort_month.date()],
            )
            for row in rows
            if 0 <= int(row.month_number) <= 11 and row.cohort_month.date() in cohort_sizes
        ]

    async def get_data_freshness(self) -> DataFreshness:
        async with self._session_factory() as session:
            imported_at = await session.scalar(
                select(DatasetMetadata.last_imported_at).where(
                    DatasetMetadata.dataset_name == "olist"
                )
            )
        return DataFreshness(last_imported_at=imported_at)

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


def _build_log_normal_fit(*, values: list[float]) -> LogNormalFit:
    sample_size = len(values)
    if sample_size < 2:
        return _unavailable_log_normal_fit(sample_size=sample_size)

    log_values = [math.log(value) for value in values]
    mu = sum(log_values) / sample_size
    variance = sum((value - mu) ** 2 for value in log_values) / sample_size
    sigma = math.sqrt(variance)
    if sigma <= 0:
        return _unavailable_log_normal_fit(sample_size=sample_size)

    sum_squared_deviations = sum((value - mu) ** 2 for value in log_values)
    log_likelihood = (
        -sample_size * math.log(sigma)
        - sample_size * math.log(2 * math.pi) / 2
        - sum(log_values)
        - sum_squared_deviations / (2 * variance)
    )
    minimum, maximum = values[0], values[-1]
    density_points = [
        LogNormalDensityPoint(
            order_value=_money_from_float(value),
            density=(
                math.exp(-((math.log(value) - mu) ** 2) / (2 * variance))
                / (value * sigma * math.sqrt(2 * math.pi))
            ),
        )
        for value in _linspace(start=minimum, stop=maximum, count=41)
        if value > 0
    ]
    kde_points = _build_log_kde_points(
        values=values,
        log_values=log_values,
        sigma=sigma,
    )
    normal_distribution = NormalDist()
    point_count = min(sample_size, 25)
    qq_points = [
        LogNormalQuantilePoint(
            theoretical_value=_money_from_float(
                math.exp(mu + sigma * normal_distribution.inv_cdf((index + 0.5) / point_count))
            ),
            observed_value=_money_from_float(
                _interpolated_quantile(values=values, probability=(index + 0.5) / point_count)
            ),
        )
        for index in range(point_count)
    ]
    parameter_count = 2
    return LogNormalFit(
        sample_size=sample_size,
        mu=mu,
        sigma=sigma,
        log_likelihood=log_likelihood,
        aic=2 * parameter_count - 2 * log_likelihood,
        bic=math.log(sample_size) * parameter_count - 2 * log_likelihood,
        density_points=density_points,
        kde_points=kde_points,
        qq_points=qq_points,
    )


def _unavailable_log_normal_fit(*, sample_size: int) -> LogNormalFit:
    return LogNormalFit(
        sample_size=sample_size,
        mu=None,
        sigma=None,
        log_likelihood=None,
        aic=None,
        bic=None,
        density_points=[],
        kde_points=[],
        qq_points=[],
    )


def _interpolated_quantile(*, values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return values[lower_index]
    weight = position - lower_index
    return values[lower_index] * (1 - weight) + values[upper_index] * weight


def _linspace(*, start: float, stop: float, count: int) -> list[float]:
    if start == stop:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * index for index in range(count)]


def _build_log_kde_points(
    *,
    values: list[float],
    log_values: list[float],
    sigma: float,
) -> list[KernelDensityPoint]:
    """Estimate an order-value density on log values with Silverman's bandwidth.

    A fixed, evenly spaced sample protects the dashboard endpoint from doing millions of
    exponentials when the complete Olist dataset is imported, without changing the displayed
    curve materially.
    """
    maximum_sample_size = 10_000
    sample_step = max(1, math.ceil(len(log_values) / maximum_sample_size))
    sample = log_values[::sample_step]
    sample_size = len(sample)
    bandwidth = 1.06 * sigma * sample_size ** (-1 / 5)
    if bandwidth <= 0:
        return []

    normalizer = sample_size * bandwidth * math.sqrt(2 * math.pi)
    return [
        KernelDensityPoint(
            order_value=_money_from_float(value),
            density=sum(
                math.exp(-0.5 * ((math.log(value) - log_value) / bandwidth) ** 2)
                for log_value in sample
            )
            / (normalizer * value),
        )
        for value in _linspace(start=values[0], stop=values[-1], count=41)
        if value > 0
    ]


def _money_from_float(value: float) -> Money:
    return Money(amount=Decimal(str(value)))
