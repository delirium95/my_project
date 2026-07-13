from abc import ABC, abstractmethod

from boutique.domain.common.repository import AbstractRepository
from boutique.domain.ids import UserID
from boutique.domain.users.models import User


class UserRepository(AbstractRepository[UserID, User], ABC):
    @abstractmethod
    async def create(self, *, user: User) -> User:
        """Persist a new user and return its canonical stored representation."""

    @abstractmethod
    async def get_by_email(self, *, email: str) -> User | None:
        """Return a user by normalized email, if one exists."""
