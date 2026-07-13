from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from boutique.domain.auth.exceptions import EmailAlreadyRegisteredError
from boutique.domain.ids import AuthSubject, UserID
from boutique.domain.users.interfaces import UserRepository
from boutique.domain.users.models import User as UserAggregate
from boutique.infrastructure.database.models import User as UserRecord


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, *, session: AsyncSession) -> None:
        self._session = session

    async def add(self, *, aggregate: UserAggregate) -> None:
        record = await self._session.get(UserRecord, aggregate.id)
        if record is None:
            self._session.add(self._to_record(user=aggregate))
            return
        record.auth_subject = aggregate.auth_subject
        record.email = aggregate.email
        record.display_name = aggregate.display_name
        record.password_hash = aggregate.password_hash
        record.is_active = aggregate.is_active

    async def create(self, *, user: UserAggregate) -> UserAggregate:
        self._session.add(self._to_record(user=user))
        try:
            await self._session.flush()
        except IntegrityError as error:
            raise EmailAlreadyRegisteredError(
                "An account with this email already exists"
            ) from error
        return user

    async def get(self, *, identity: UserID) -> UserAggregate | None:
        record = await self._session.get(UserRecord, identity)
        return self._to_aggregate(record=record) if record else None

    async def get_by_email(self, *, email: str) -> UserAggregate | None:
        record = await self._session.scalar(select(UserRecord).where(UserRecord.email == email))
        return self._to_aggregate(record=record) if record else None

    @staticmethod
    def _to_record(*, user: UserAggregate) -> UserRecord:
        return UserRecord(
            id=user.id,
            auth_subject=user.auth_subject,
            email=user.email,
            display_name=user.display_name,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )

    @staticmethod
    def _to_aggregate(*, record: UserRecord) -> UserAggregate:
        return UserAggregate(
            id=UserID(record.id),
            auth_subject=AuthSubject(record.auth_subject),
            email=record.email,
            display_name=record.display_name,
            password_hash=record.password_hash,
            is_active=record.is_active,
        )
