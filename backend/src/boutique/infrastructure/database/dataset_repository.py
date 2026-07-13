from collections.abc import Iterator
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from boutique.domain.dataset.exceptions import DatasetAlreadySeededError
from boutique.domain.dataset.interfaces import DatasetRepository
from boutique.domain.dataset.models import OlistDataset, SeedResult
from boutique.infrastructure.database.models import Customer, Order, OrderItem, Product

_BATCH_SIZE = 5_000


class SqlAlchemyDatasetRepository(DatasetRepository):
    """Bulk persistence adapter; its transaction is owned by the shared UoW."""

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def replace_olist(
        self,
        *,
        dataset: OlistDataset,
        replace_existing: bool,
    ) -> SeedResult:
        await self._guard_or_reset(replace_existing=replace_existing)
        await self._insert_in_batches(model=Customer, rows=dataset.customers)
        await self._insert_in_batches(model=Product, rows=dataset.products)
        await self._insert_in_batches(model=Order, rows=dataset.orders)
        await self._insert_in_batches(model=OrderItem, rows=dataset.order_items)
        return SeedResult(
            customers=len(dataset.customers),
            products=len(dataset.products),
            orders=len(dataset.orders),
            order_items=len(dataset.order_items),
        )

    async def _guard_or_reset(self, *, replace_existing: bool) -> None:
        existing_orders = await self._session.scalar(select(func.count()).select_from(Order))
        if existing_orders and not replace_existing:
            raise DatasetAlreadySeededError(
                "The dataset is already seeded. Re-run with --replace to discard and reload it."
            )
        if existing_orders:
            await self._session.execute(
                text(
                    "TRUNCATE TABLE order_items, orders, products, customers "
                    "RESTART IDENTITY CASCADE"
                )
            )

    async def _insert_in_batches(
        self,
        *,
        model: type[Customer] | type[Product] | type[Order] | type[OrderItem],
        rows: list[dict[str, Any]],
    ) -> None:
        for batch in _batched(rows=rows, size=_BATCH_SIZE):
            await self._session.execute(model.__table__.insert(), batch)


def _batched(*, rows: list[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    for index in range(0, len(rows), size):
        yield rows[index : index + size]
