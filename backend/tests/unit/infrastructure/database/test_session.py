import ssl

import pytest

from boutique.infrastructure.database import session
from boutique.infrastructure.database.session import (
    create_database_engine,
    normalize_async_database_url,
)


def test_normalizes_a_managed_postgres_url_for_asyncpg() -> None:
    url, connect_args = normalize_async_database_url(
        "postgresql://user:password@ep-example.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )

    assert url.drivername == "postgresql+asyncpg"
    assert not url.query
    assert "ssl" in connect_args


def test_uses_packaged_rds_ca_bundle_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str | None] = {}

    def create_ssl_context(*, cafile: str | None = None) -> ssl.SSLContext:
        captured["cafile"] = cafile
        return ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    monkeypatch.setattr(
        session,
        "_rds_ca_bundle_path",
        lambda: "/var/task/rds-global-bundle.pem",
    )
    monkeypatch.setattr(session.ssl, "create_default_context", create_ssl_context)

    _, connect_args = normalize_async_database_url(
        "postgresql://user:password@db.example.com/database?sslmode=require"
    )

    assert captured["cafile"] == "/var/task/rds-global-bundle.pem"
    assert "ssl" in connect_args


@pytest.mark.asyncio
async def test_database_engine_accepts_a_managed_postgres_url() -> None:
    engine = create_database_engine(
        database_url="postgresql://user:password@db.example.com/database?sslmode=require",
        serverless=True,
    )

    assert engine.url.drivername == "postgresql+asyncpg"
    await engine.dispose()
