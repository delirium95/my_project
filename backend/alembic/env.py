import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from boutique.config import get_settings
from boutique.infrastructure.database.base import Base
from boutique.infrastructure.database.session import normalize_async_database_url
import boutique.infrastructure.database.models  # noqa: F401 - registers model metadata for Alembic

config = context.config
settings = get_settings()
database_url, database_connect_args = normalize_async_database_url(settings.database_url)
# ``str(URL)`` intentionally masks the password as ``***``. Alembic later reads this
# value back to create its engine, so pass an unmasked URL only to its in-process config.
config.set_main_option("sqlalchemy.url", database_url.render_as_string(hide_password=False))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=database_connect_args,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
