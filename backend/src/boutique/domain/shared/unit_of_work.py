from abc import ABC, abstractmethod
from types import TracebackType
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from boutique.domain.dataset.interfaces import DatasetRepository
    from boutique.domain.orders.interfaces import OrderRepository
    from boutique.domain.users.interfaces import UserRepository


class UnitOfWork(ABC):
    """Single application transaction contract containing all write repositories.

    New write repositories belong here as the application grows; commands never create
    aggregate-specific UoWs. This template makes nested contexts re-entrant without
    splitting the underlying transaction.
    """

    orders: "OrderRepository"
    dataset: "DatasetRepository"
    users: "UserRepository"

    def __init__(self) -> None:
        self._depth = 0
        self._commit_requested = False
        self._committed = False
        self._rollback_only = False

    @property
    def depth(self) -> int:
        """The number of active nested contexts for this UoW."""
        return self._depth

    @property
    def is_committed(self) -> bool:
        return self._committed

    @property
    def is_rollback_only(self) -> bool:
        return self._rollback_only

    async def __aenter__(self) -> Self:
        if self._depth == 0:
            self._commit_requested = False
            self._committed = False
            self._rollback_only = False
            await self._open()
        self._depth += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._depth == 0:
            raise RuntimeError("Unit of work exit without a matching enter")
        if exc_type is not None:
            self._rollback_only = True
        self._depth -= 1
        if self._depth:
            return

        try:
            if self._rollback_only or not self._commit_requested:
                await self._rollback()
            else:
                await self._commit()
                self._committed = True
        except Exception:
            self._rollback_only = True
            await self._rollback()
            raise
        finally:
            await self._close()

    async def commit(self) -> None:
        """Request one commit when the outermost context closes."""
        if self._depth == 0:
            raise RuntimeError('Use "async with uow" before committing')
        if self._rollback_only:
            raise RuntimeError("Unit of work is rollback-only and cannot be committed")
        self._commit_requested = True

    async def rollback(self) -> None:
        """Mark the entire re-entrant transaction for rollback."""
        self._rollback_only = True

    @abstractmethod
    async def _open(self) -> None:
        """Open the backing transaction and initialize all repositories once."""

    @abstractmethod
    async def _commit(self) -> None:
        """Commit the backing transaction at the outermost boundary."""

    @abstractmethod
    async def _rollback(self) -> None:
        """Rollback the backing transaction at the outermost boundary."""

    @abstractmethod
    async def _close(self) -> None:
        """Release the backing transaction resources at the outermost boundary."""
