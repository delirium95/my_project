from boutique.domain.dataset.interfaces import DatasetRepository
from boutique.domain.dataset.models import OlistDataset, SeedResult
from boutique.domain.ids import OrderID, UserID
from boutique.domain.orders.interfaces import OrderRepository
from boutique.domain.orders.models import Order
from boutique.domain.shared.unit_of_work import UnitOfWork
from boutique.domain.users.interfaces import UserRepository
from boutique.domain.users.models import User


class InMemoryOrderRepository(OrderRepository):
    def __init__(self) -> None:
        self.orders: dict[OrderID, Order] = {}

    async def get(self, *, identity: OrderID) -> Order | None:
        return self.orders.get(identity)

    async def add(self, *, aggregate: Order) -> None:
        self.orders[aggregate.id] = aggregate

    async def replace(self, *, aggregate: Order) -> None:
        self.orders[aggregate.id] = aggregate


class InMemoryDatasetRepository(DatasetRepository):
    def __init__(self) -> None:
        self.request: tuple[OlistDataset, bool] | None = None

    async def replace_olist(
        self,
        *,
        dataset: OlistDataset,
        replace_existing: bool,
    ) -> SeedResult:
        self.request = (dataset, replace_existing)
        return SeedResult(
            customers=len(dataset.customers),
            products=len(dataset.products),
            orders=len(dataset.orders),
            order_items=len(dataset.order_items),
        )


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[UserID, User] = {}

    async def add(self, *, aggregate: User) -> None:
        self.users[aggregate.id] = aggregate

    async def create(self, *, user: User) -> User:
        self.users[user.id] = user
        return user

    async def get(self, *, identity: UserID) -> User | None:
        return self.users.get(identity)

    async def get_by_email(self, *, email: str) -> User | None:
        return next((user for user in self.users.values() if user.email == email), None)


class FakeUnitOfWork(UnitOfWork):
    """Test double for the exact production UoW abstraction, not a lookalike."""

    def __init__(self) -> None:
        super().__init__()
        self.dataset = InMemoryDatasetRepository()
        self.orders = InMemoryOrderRepository()
        self.users = InMemoryUserRepository()
        self.open_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    async def _open(self) -> None:
        self.open_count += 1

    async def _commit(self) -> None:
        self.commit_count += 1

    async def _rollback(self) -> None:
        self.rollback_count += 1

    async def _close(self) -> None:
        self.close_count += 1
