from abc import ABC, abstractmethod


class AbstractRepository[IdentityT, AggregateT](ABC):
    """Base repository contract, following the Stock Picker repository pattern."""

    @abstractmethod
    async def add(self, *, aggregate: AggregateT) -> None:
        """Stage a new aggregate in the active unit of work."""

    @abstractmethod
    async def get(self, *, identity: IdentityT) -> AggregateT | None:
        """Return one aggregate by its typed identity, when it exists."""
