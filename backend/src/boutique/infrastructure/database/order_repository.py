from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from boutique.domain.common.value_objects import Money
from boutique.domain.ids import CustomerID, OrderID, ProductID
from boutique.domain.orders.enums import OrderStatus
from boutique.domain.orders.interfaces import OrderRepository
from boutique.domain.orders.models import Order as OrderAggregate
from boutique.domain.orders.models import OrderItem
from boutique.infrastructure.database.models import Order as OrderRecord
from boutique.infrastructure.database.models import OrderItem as OrderItemRecord


class SqlAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy mapper for the Order aggregate; no query projections belong here."""

    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def get(self, *, identity: OrderID) -> OrderAggregate | None:
        record = await self._session.get(OrderRecord, identity)
        if record is None:
            return None
        item_records = (
            await self._session.scalars(
                select(OrderItemRecord).where(OrderItemRecord.order_id == record.id)
            )
        ).all()
        return OrderAggregate(
            id=OrderID(record.id),
            customer_id=CustomerID(record.customer_id),
            purchased_at=record.purchased_at,
            status=OrderStatus(record.status),
            delivered_at=record.delivered_at,
            items=tuple(
                OrderItem(
                    product_id=ProductID(item.product_id),
                    unit_price=Money(amount=item.price),
                    freight=Money(amount=item.freight_value),
                    quantity=item.quantity,
                )
                for item in item_records
            ),
        )

    async def add(self, *, aggregate: OrderAggregate) -> None:
        self._session.add(
            OrderRecord(
                id=aggregate.id,
                customer_id=aggregate.customer_id,
                status=aggregate.status.value,
                purchased_at=aggregate.purchased_at,
                delivered_at=aggregate.delivered_at,
            )
        )
        self._add_items(aggregate=aggregate)

    async def replace(self, *, aggregate: OrderAggregate) -> None:
        record = await self._session.get(OrderRecord, aggregate.id)
        if record is None:
            await self.add(aggregate=aggregate)
            return
        record.customer_id = aggregate.customer_id
        record.status = aggregate.status.value
        record.purchased_at = aggregate.purchased_at
        record.delivered_at = aggregate.delivered_at
        await self._session.execute(
            delete(OrderItemRecord).where(OrderItemRecord.order_id == aggregate.id)
        )
        self._add_items(aggregate=aggregate)

    def _add_items(self, *, aggregate: OrderAggregate) -> None:
        self._session.add_all(
            [
                OrderItemRecord(
                    order_id=aggregate.id,
                    line_number=index,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.unit_price.amount,
                    freight_value=item.freight.amount,
                )
                for index, item in enumerate(aggregate.items, start=1)
            ]
        )
