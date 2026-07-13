from datetime import UTC, datetime
from decimal import Decimal

import pytest

from boutique.application.orders.use_cases import UpsertOrderUseCaseImpl
from boutique.domain.common.value_objects import Money
from boutique.domain.ids import CustomerID, OrderID, ProductID
from boutique.domain.orders.models import Order, OrderItem
from tests.fakes.unit_of_work import FakeUnitOfWork


@pytest.mark.unit
async def test_upsert_order_commits_aggregate_in_one_unit_of_work() -> None:
    order = Order(
        id=OrderID("order-1"),
        customer_id=CustomerID("customer-1"),
        purchased_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    order.add_item(
        item=OrderItem(
            product_id=ProductID("product-1"),
            unit_price=Money(amount=Decimal("10")),
            freight=Money(amount=Decimal("2")),
        )
    )
    unit_of_work = FakeUnitOfWork()

    await UpsertOrderUseCaseImpl(unit_of_work=unit_of_work)(order=order)

    assert unit_of_work.is_committed
    assert unit_of_work.commit_count == 1
    assert unit_of_work.orders.orders == {OrderID("order-1"): order}


@pytest.mark.unit
async def test_nested_contexts_share_one_transaction_and_commit_only_at_outer_exit() -> None:
    unit_of_work = FakeUnitOfWork()

    async with unit_of_work:
        assert unit_of_work.depth == 1
        async with unit_of_work:
            assert unit_of_work.depth == 2
            await unit_of_work.commit()
            assert unit_of_work.commit_count == 0
        assert unit_of_work.depth == 1
        assert unit_of_work.commit_count == 0

    assert unit_of_work.depth == 0
    assert unit_of_work.commit_count == 1
    assert unit_of_work.close_count == 1


@pytest.mark.unit
async def test_nested_exception_marks_uow_rollback_only_even_when_caught() -> None:
    unit_of_work = FakeUnitOfWork()

    async with unit_of_work:
        try:
            async with unit_of_work:
                raise ValueError("inner failure")
        except ValueError:
            pass

        assert unit_of_work.is_rollback_only
        with pytest.raises(RuntimeError, match="rollback-only"):
            await unit_of_work.commit()

    assert unit_of_work.rollback_count == 1
    assert unit_of_work.close_count == 1
