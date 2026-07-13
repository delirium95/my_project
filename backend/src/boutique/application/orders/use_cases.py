from boutique.application.orders.interfaces import UpsertOrderUseCase
from boutique.domain.orders.models import Order
from boutique.domain.shared.unit_of_work import UnitOfWork


class UpsertOrderUseCaseImpl(UpsertOrderUseCase):
    """Write use case used by the dataset importer, never by HTTP read routes."""

    def __init__(self, *, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def __call__(self, *, order: Order) -> None:
        async with self._unit_of_work as unit_of_work:
            existing_order = await unit_of_work.orders.get(identity=order.id)
            if existing_order is None:
                await unit_of_work.orders.add(aggregate=order)
            else:
                await unit_of_work.orders.replace(aggregate=order)
            await unit_of_work.commit()
