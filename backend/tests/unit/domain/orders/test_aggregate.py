from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from boutique.domain.common.exceptions import DomainValidationError
from boutique.domain.common.value_objects import Money
from boutique.domain.ids import CustomerID, OrderID, ProductID
from boutique.domain.orders.enums import OrderStatus
from boutique.domain.orders.models import Order, OrderItem


@pytest.mark.unit
def test_order_aggregate_calculates_total_and_prevents_post_delivery_mutation() -> None:
    purchased_at = datetime(2025, 1, 1, tzinfo=UTC)
    order = Order(
        id=OrderID("order-1"),
        customer_id=CustomerID("customer-1"),
        purchased_at=purchased_at,
    )
    order.add_item(
        item=OrderItem(
            product_id=ProductID("product-1"),
            unit_price=Money(amount=Decimal("10.00")),
            freight=Money(amount=Decimal("2.50")),
            quantity=2,
        )
    )

    assert order.total == Money(amount=Decimal("22.50"))

    order.mark_delivered(delivered_at=purchased_at + timedelta(days=1))

    assert order.status is OrderStatus.DELIVERED
    with pytest.raises(DomainValidationError, match="Cannot modify"):
        order.add_item(
            item=OrderItem(
                product_id=ProductID("product-2"),
                unit_price=Money(amount=Decimal("1")),
                freight=Money(amount=Decimal("0")),
            )
        )


@pytest.mark.unit
def test_money_rejects_mixed_currencies() -> None:
    with pytest.raises(DomainValidationError, match="different currencies"):
        Money(amount=Decimal("1"), currency="BRL").add(
            other=Money(amount=Decimal("1"), currency="USD")
        )
