"""Black-box HTTP tests against the local PostgreSQL and Redis services."""

import asyncio
import os
from datetime import UTC, datetime
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis
from sqlalchemy import delete

from boutique.config import Settings
from boutique.infrastructure.database.models import (
    Customer,
    Order,
    OrderItem,
    Product,
)
from boutique.infrastructure.database.models import (
    User as UserRecord,
)
from boutique.infrastructure.database.session import create_database_engine, make_session_factory
from boutique.main import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason="set RUN_INTEGRATION_TESTS=1 after docker compose up -d",
    ),
]


@pytest.fixture
def integration_settings() -> Settings:
    local_settings = Settings()
    return Settings(
        database_url=local_settings.database_url,
        environment="integration",
        jwt_secret="integration-tests-only-very-long-secret-change-me-before-production",
        cookie_secure=False,
        redis_url=_integration_redis_url(redis_url=local_settings.redis_url),
        serverless=local_settings.serverless,
        kaggle_username=None,
        kaggle_key=None,
    )


@pytest.fixture
def client(integration_settings: Settings) -> TestClient:
    with TestClient(create_app(settings=integration_settings)) as test_client:
        yield test_client
    asyncio.run(_delete_integration_users(settings=integration_settings))
    asyncio.run(_clear_integration_redis(settings=integration_settings))


@pytest.fixture
def seeded_eda_data(integration_settings: Settings) -> None:
    fixture_ids = asyncio.run(_insert_eda_fixture(settings=integration_settings))
    try:
        yield
    finally:
        asyncio.run(_delete_eda_fixture(settings=integration_settings, fixture_ids=fixture_ids))


def test_authentication_refresh_rotation_and_logout(client: TestClient) -> None:
    email = _test_email()
    password = "correct-horse-battery-staple"

    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Integration User"},
    )
    assert registered.status_code == 201
    registered_user = registered.json()
    assert registered_user["id"]
    assert registered_user["email"] == email
    assert registered_user["display_name"] == "Integration User"

    logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert logged_in.status_code == 200
    token = logged_in.json()["access_token"]
    assert client.cookies.get("refresh_token") is not None

    current_user = client.get("/api/v1/auth/me", headers=_bearer_headers(token=token))
    assert current_user.status_code == 200
    assert current_user.json()["email"] == email

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != token
    assert client.cookies.get("refresh_token") is not None

    logged_out = client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 204
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_dashboard_is_protected_and_uses_real_read_adapters(client: TestClient) -> None:
    email = _test_email()
    password = "correct-horse-battery-staple"
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "display_name": "Dashboard User"},
        ).status_code
        == 201
    )
    logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = _bearer_headers(token=logged_in.json()["access_token"])

    assert client.get("/api/v1/dashboard/summary").status_code == 401

    readiness = client.get("/api/v1/health/ready")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "healthy"

    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert set(summary.json()) == {"revenue", "delivered_orders", "average_order_value"}

    revenue = client.get("/api/v1/dashboard/revenue", headers=headers)
    assert revenue.status_code == 200
    assert isinstance(revenue.json(), list)

    orders = client.get("/api/v1/dashboard/orders?limit=3", headers=headers)
    assert orders.status_code == 200
    assert isinstance(orders.json(), list)


def test_kaggle_import_requires_server_credentials(client: TestClient) -> None:
    email = _test_email()
    password = "correct-horse-battery-staple"
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password},
        ).status_code
        == 201
    )
    logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})

    response = client.post(
        "/api/v1/dataset/import/kaggle",
        headers=_bearer_headers(token=logged_in.json()["access_token"]),
        json={"replace_existing": False},
    )

    assert response.status_code == 503
    assert "KAGGLE_USERNAME" in response.json()["detail"]


def test_dashboard_eda_returns_statistical_analytics(
    client: TestClient,
    seeded_eda_data: None,
) -> None:
    email = _test_email()
    password = "correct-horse-battery-staple"
    registered = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert registered.status_code == 201
    logged_in = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    headers = _bearer_headers(token=logged_in.json()["access_token"])

    distribution = client.get("/api/v1/dashboard/distribution", headers=headers)
    assert distribution.status_code == 200
    assert len(distribution.json()) == 10
    assert sum(item["order_count"] for item in distribution.json()) >= 3

    correlations = client.get("/api/v1/dashboard/correlations", headers=headers)
    assert correlations.status_code == 200
    assert len(correlations.json()) == 16
    items_diagonal = next(
        item for item in correlations.json() if item["x"] == "Items" and item["y"] == "Items"
    )
    assert items_diagonal["coefficient"] == pytest.approx(1.0)

    log_normal_fit = client.get("/api/v1/dashboard/fit/log-normal", headers=headers)
    assert log_normal_fit.status_code == 200
    fit = log_normal_fit.json()
    assert fit["sample_size"] == 3
    assert fit["log_likelihood"] is not None
    assert len(fit["density_points"]) == 41
    assert len(fit["kde_points"]) == 41
    assert len(fit["qq_points"]) == 3

    pareto = client.get("/api/v1/dashboard/pareto", headers=headers)
    assert pareto.status_code == 200
    pareto_points = pareto.json()
    assert len(pareto_points) == 1
    assert pareto_points[0]["category"] == "books"
    assert float(pareto_points[0]["revenue"]) == pytest.approx(382.0)
    assert pareto_points[0]["cumulative_share"] == pytest.approx(1.0)

    cohorts = client.get("/api/v1/dashboard/cohorts", headers=headers)
    assert cohorts.status_code == 200
    cohort_points = cohorts.json()
    february_cohort = next(
        point
        for point in cohort_points
        if point["cohort_month"] == "2017-02-01" and point["month_number"] == 1
    )
    assert february_cohort["retention_rate"] == pytest.approx(1.0)

    freshness = client.get("/api/v1/dashboard/data-freshness", headers=headers)
    assert freshness.status_code == 200
    assert "last_imported_at" in freshness.json()

    invalid_range = client.get(
        "/api/v1/dashboard/correlations?start_date=2018-01-02&end_date=2018-01-01",
        headers=headers,
    )
    assert invalid_range.status_code == 422


def _test_email() -> str:
    return f"integration-{uuid4().hex}@example.com"


def _bearer_headers(*, token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _delete_integration_users(*, settings: Settings) -> None:
    engine = create_database_engine(
        database_url=settings.database_url,
        serverless=settings.serverless,
    )
    session_factory = make_session_factory(engine=engine)
    try:
        async with session_factory() as session:
            await session.execute(
                delete(UserRecord).where(UserRecord.email.like("integration-%@example.com"))
            )
            await session.commit()
    finally:
        await engine.dispose()


async def _clear_integration_redis(*, settings: Settings) -> None:
    client = Redis.from_url(url=settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        await client.flushdb()
    finally:
        await client.aclose()


async def _insert_eda_fixture(*, settings: Settings) -> dict[str, list[str] | str]:
    suffix = uuid4().hex
    customer_ids = [f"integration-customer-{suffix}-{index}" for index in range(1, 4)]
    order_ids = [f"integration-order-{suffix}-{index}" for index in range(1, 4)]
    product_id = f"integration-product-{suffix}"
    engine = create_database_engine(
        database_url=settings.database_url,
        serverless=settings.serverless,
    )
    session_factory = make_session_factory(engine=engine)
    try:
        async with session_factory() as session:
            session.add_all(
                [
                    Customer(
                        id=customer_id,
                        unique_id=("integration-repeat-customer" if index > 1 else customer_id),
                        state="SP",
                    )
                    for index, customer_id in enumerate(customer_ids, start=1)
                ]
            )
            session.add(Product(id=product_id, category="books"))
            session.add_all(
                [
                    Order(
                        id=order_ids[0],
                        customer_id=customer_ids[0],
                        status="delivered",
                        purchased_at=datetime(2017, 1, 1, tzinfo=UTC),
                    ),
                    Order(
                        id=order_ids[1],
                        customer_id=customer_ids[1],
                        status="delivered",
                        purchased_at=datetime(2017, 2, 1, tzinfo=UTC),
                    ),
                    Order(
                        id=order_ids[2],
                        customer_id=customer_ids[2],
                        status="delivered",
                        purchased_at=datetime(2017, 3, 1, tzinfo=UTC),
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    OrderItem(
                        order_id=order_ids[0],
                        line_number=1,
                        product_id=product_id,
                        price=50,
                        freight_value=5,
                    ),
                    OrderItem(
                        order_id=order_ids[1],
                        line_number=1,
                        product_id=product_id,
                        price=40,
                        freight_value=8,
                    ),
                    OrderItem(
                        order_id=order_ids[1],
                        line_number=2,
                        product_id=product_id,
                        price=60,
                        freight_value=10,
                    ),
                    OrderItem(
                        order_id=order_ids[2],
                        line_number=1,
                        product_id=product_id,
                        price=30,
                        freight_value=2,
                    ),
                    OrderItem(
                        order_id=order_ids[2],
                        line_number=2,
                        product_id=product_id,
                        price=70,
                        freight_value=12,
                    ),
                    OrderItem(
                        order_id=order_ids[2],
                        line_number=3,
                        product_id=product_id,
                        price=80,
                        freight_value=15,
                    ),
                ]
            )
            await session.commit()
    finally:
        await engine.dispose()
    return {"customer_ids": customer_ids, "order_ids": order_ids, "product_id": product_id}


async def _delete_eda_fixture(
    *,
    settings: Settings,
    fixture_ids: dict[str, list[str] | str],
) -> None:
    engine = create_database_engine(
        database_url=settings.database_url,
        serverless=settings.serverless,
    )
    session_factory = make_session_factory(engine=engine)
    try:
        async with session_factory() as session:
            order_ids = fixture_ids["order_ids"]
            customer_ids = fixture_ids["customer_ids"]
            product_id = fixture_ids["product_id"]
            assert isinstance(order_ids, list)
            assert isinstance(customer_ids, list)
            assert isinstance(product_id, str)
            await session.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
            await session.execute(delete(Order).where(Order.id.in_(order_ids)))
            await session.execute(delete(Product).where(Product.id == product_id))
            await session.execute(delete(Customer).where(Customer.id.in_(customer_ids)))
            await session.commit()
    finally:
        await engine.dispose()


def _integration_redis_url(*, redis_url: str) -> str:
    parsed_url = urlsplit(redis_url)
    return urlunsplit(parsed_url._replace(path="/15"))
