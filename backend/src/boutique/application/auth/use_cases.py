from uuid import UUID, uuid4

from boutique.application.auth.interfaces import (
    GetCurrentUserUseCase,
    LoginUseCase,
    LogoutUseCase,
    RefreshTokenUseCase,
    RegisterUserUseCase,
)
from boutique.domain.auth.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError
from boutique.domain.auth.interfaces import PasswordHasher, TokenService
from boutique.domain.auth.models import LoginInput, RegisterUserInput, TokenPair
from boutique.domain.ids import AuthSubject, UserID
from boutique.domain.shared.unit_of_work import UnitOfWork
from boutique.domain.users.models import User


class RegisterUserUseCaseImpl(RegisterUserUseCase):
    def __init__(self, *, password_hasher: PasswordHasher, unit_of_work: UnitOfWork) -> None:
        self._password_hasher = password_hasher
        self._unit_of_work = unit_of_work

    async def __call__(self, *, input_data: RegisterUserInput) -> User:
        user_id = UserID(uuid4())
        user = User(
            id=user_id,
            auth_subject=AuthSubject(f"local|{user_id}"),
            email=input_data.email,
            display_name=input_data.display_name,
            password_hash=self._password_hasher.hash(password=input_data.password),
        )
        async with self._unit_of_work as unit_of_work:
            if await unit_of_work.users.get_by_email(email=user.email):
                raise EmailAlreadyRegisteredError("An account with this email already exists")
            created_user = await unit_of_work.users.create(user=user)
            await unit_of_work.commit()
        return created_user


class LoginUseCaseImpl(LoginUseCase):
    def __init__(
        self,
        *,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._unit_of_work = unit_of_work

    async def __call__(self, *, input_data: LoginInput) -> TokenPair:
        async with self._unit_of_work as unit_of_work:
            user = await unit_of_work.users.get_by_email(email=input_data.email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("Invalid email or password")
        self._password_hasher.verify(
            password=input_data.password,
            password_hash=user.password_hash,
        )
        return self._token_service.issue(user_id=user.id)


class RefreshTokenUseCaseImpl(RefreshTokenUseCase):
    def __init__(self, *, token_service: TokenService) -> None:
        self._token_service = token_service

    async def __call__(self, *, refresh_token: str) -> TokenPair:
        return await self._token_service.rotate_refresh(refresh_token=refresh_token)


class LogoutUseCaseImpl(LogoutUseCase):
    def __init__(self, *, token_service: TokenService) -> None:
        self._token_service = token_service

    async def __call__(self, *, refresh_token: str) -> None:
        await self._token_service.revoke_refresh(refresh_token=refresh_token)


class GetCurrentUserUseCaseImpl(GetCurrentUserUseCase):
    def __init__(self, *, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def __call__(self, *, user_id: str) -> User:
        parsed_user_id = UserID(UUID(user_id))
        async with self._unit_of_work as unit_of_work:
            user = await unit_of_work.users.get(identity=parsed_user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError("Invalid authenticated user")
        return user
