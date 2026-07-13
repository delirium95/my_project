from abc import ABC, abstractmethod

from boutique.domain.common.repository import AbstractRepository
from boutique.domain.ids import OrderID
from boutique.domain.orders.models import Order


class OrderRepository(AbstractRepository[OrderID, Order], ABC):
    """Collection-like contract for the Order aggregate root only."""

    @abstractmethod
    async def get(self, *, identity: OrderID) -> Order | None:
        """Return an aggregate by identity, if it exists."""

    @abstractmethod
    async def add(self, *, aggregate: Order) -> None:
        """Stage a new aggregate in the current transaction."""

    @abstractmethod
    async def replace(self, *, aggregate: Order) -> None:
        """Stage an existing aggregate's new state in the current transaction."""
