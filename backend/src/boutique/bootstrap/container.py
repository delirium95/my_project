from dependency_injector import containers, providers
from redis.asyncio import Redis

from boutique.application.auth.use_cases import (
    GetCurrentUserUseCaseImpl,
    LoginUseCaseImpl,
    LogoutUseCaseImpl,
    RefreshTokenUseCaseImpl,
    RegisterUserUseCaseImpl,
)
from boutique.application.dashboard.use_cases import (
    GetDashboardSummaryUseCaseImpl,
    GetMonthlyRevenueUseCaseImpl,
    GetOrderValueDistributionUseCaseImpl,
    GetPearsonCorrelationsUseCaseImpl,
    ListRecentOrdersUseCaseImpl,
)
from boutique.application.dataset.use_cases import (
    ImportKaggleOlistDatasetUseCaseImpl,
    SeedOlistDatasetUseCaseImpl,
)
from boutique.application.health.use_cases import GetReadinessUseCaseImpl
from boutique.application.orders.use_cases import UpsertOrderUseCaseImpl
from boutique.config import Settings
from boutique.infrastructure.auth.argon2_password_hasher import Argon2PasswordHasher
from boutique.infrastructure.auth.jwt_token_service import JwtTokenService
from boutique.infrastructure.auth.redis_refresh_token_blacklist import RedisRefreshTokenBlacklist
from boutique.infrastructure.cache.redis_cache_service import RedisCacheService
from boutique.infrastructure.database.dashboard_query_service import SqlAlchemyDashboardQueryService
from boutique.infrastructure.database.session import create_database_engine, make_session_factory
from boutique.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from boutique.infrastructure.dataset.kaggle_olist_archive import KaggleOlistArchiveDownloaderImpl
from boutique.infrastructure.dataset.olist_csv_source import OlistCsvSource
from boutique.infrastructure.health.checkers import PostgresHealthChecker, RedisHealthChecker


def make_redis_client(*, redis_url: str) -> Redis:
    return Redis.from_url(url=redis_url, encoding="utf-8", decode_responses=True)


class Container(containers.DeclarativeContainer):
    """The only place that knows which adapters implement application ports."""

    config = providers.Configuration()

    database_engine = providers.Singleton(
        create_database_engine,
        database_url=config.database_url,
        serverless=config.serverless,
    )
    session_factory = providers.Singleton(make_session_factory, engine=database_engine)
    redis_client = providers.Singleton(make_redis_client, redis_url=config.redis_url)

    dashboard_query_service = providers.Factory(
        SqlAlchemyDashboardQueryService,
        session_factory=session_factory,
    )
    cache_service = providers.Singleton(RedisCacheService, client=redis_client)
    password_hasher = providers.Singleton(Argon2PasswordHasher)
    refresh_token_blacklist = providers.Singleton(RedisRefreshTokenBlacklist, client=redis_client)
    token_service = providers.Singleton(
        JwtTokenService,
        blacklist=refresh_token_blacklist,
        secret=config.jwt_secret,
        access_ttl_minutes=config.jwt_access_ttl_minutes,
        refresh_ttl_days=config.jwt_refresh_ttl_days,
    )
    olist_source = providers.Factory(OlistCsvSource)
    kaggle_olist_archive_downloader = providers.Factory(
        KaggleOlistArchiveDownloaderImpl,
        dataset=config.kaggle_olist_dataset,
        username=config.kaggle_username,
        key=config.kaggle_key,
    )
    unit_of_work = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=session_factory,
    )

    get_dashboard_summary = providers.Factory(
        GetDashboardSummaryUseCaseImpl,
        query_service=dashboard_query_service,
        cache=cache_service,
        cache_ttl_seconds=config.dashboard_cache_ttl_seconds,
    )
    get_monthly_revenue = providers.Factory(
        GetMonthlyRevenueUseCaseImpl,
        query_service=dashboard_query_service,
        cache=cache_service,
        cache_ttl_seconds=config.dashboard_cache_ttl_seconds,
    )
    list_recent_orders = providers.Factory(
        ListRecentOrdersUseCaseImpl,
        query_service=dashboard_query_service,
    )
    get_order_value_distribution = providers.Factory(
        GetOrderValueDistributionUseCaseImpl,
        query_service=dashboard_query_service,
    )
    get_pearson_correlations = providers.Factory(
        GetPearsonCorrelationsUseCaseImpl,
        query_service=dashboard_query_service,
    )
    upsert_order = providers.Factory(UpsertOrderUseCaseImpl, unit_of_work=unit_of_work)
    register_user = providers.Factory(
        RegisterUserUseCaseImpl,
        password_hasher=password_hasher,
        unit_of_work=unit_of_work,
    )
    login = providers.Factory(
        LoginUseCaseImpl,
        password_hasher=password_hasher,
        token_service=token_service,
        unit_of_work=unit_of_work,
    )
    get_current_user = providers.Factory(GetCurrentUserUseCaseImpl, unit_of_work=unit_of_work)
    refresh_token = providers.Factory(RefreshTokenUseCaseImpl, token_service=token_service)
    logout = providers.Factory(LogoutUseCaseImpl, token_service=token_service)
    seed_olist_dataset = providers.Factory(
        SeedOlistDatasetUseCaseImpl,
        source=olist_source,
        unit_of_work=unit_of_work,
        cache=cache_service,
    )
    import_kaggle_olist_dataset = providers.Factory(
        ImportKaggleOlistDatasetUseCaseImpl,
        archive_downloader=kaggle_olist_archive_downloader,
        seed_olist_dataset=seed_olist_dataset,
    )
    get_readiness = providers.Factory(
        GetReadinessUseCaseImpl,
        environment=config.environment,
        checkers=providers.List(
            providers.Factory(PostgresHealthChecker, engine=database_engine),
            providers.Factory(RedisHealthChecker, client=redis_client),
        ),
    )


def build_container(*, settings: Settings) -> Container:
    container = Container()
    container.config.from_dict(settings.model_dump())
    return container


async def shutdown_container(*, container: Container) -> None:
    redis_client = container.redis_client()
    await redis_client.aclose()
    await container.database_engine().dispose()
