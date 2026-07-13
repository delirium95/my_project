from abc import ABC, abstractmethod

from boutique.domain.orders.models import Order


class UpsertOrderUseCase(ABC):
    @abstractmethod
    async def __call__(self, *, order: Order) -> None:
        """Persist an order aggregate in the active unit of work."""
