from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from boutique.domain.shared.unit_of_work import UnitOfWork
from boutique.infrastructure.database.dataset_repository import SqlAlchemyDatasetRepository
from boutique.infrastructure.database.order_repository import SqlAlchemyOrderRepository
from boutique.infrastructure.database.user_repository import SqlAlchemyUserRepository


class SqlAlchemyUnitOfWork(UnitOfWork):
    """One database session and one explicit commit for all command repositories."""

    def __init__(self, *, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.dataset: SqlAlchemyDatasetRepository
        self.orders: SqlAlchemyOrderRepository
        self.users: SqlAlchemyUserRepository

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError('AsyncSession is not initialized. Use "async with uow" first.')
        return self._session

    async def _open(self) -> None:
        self._session = self._session_factory()
        self.dataset = SqlAlchemyDatasetRepository(session=self._session)
        self.orders = SqlAlchemyOrderRepository(session=self._session)
        self.users = SqlAlchemyUserRepository(session=self._session)

    async def _commit(self) -> None:
        await self.session.commit()

    async def _rollback(self) -> None:
        if self._session is not None:
            await self._session.rollback()

    async def _close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None
