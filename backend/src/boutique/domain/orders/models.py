from datetime import datetime

from pydantic import Field, model_validator

from boutique.domain.common.exceptions import DomainValidationError
from boutique.domain.common.models import DomainModel, ValueObject
from boutique.domain.common.value_objects import Money
from boutique.domain.ids import CustomerID, OrderID, ProductID
from boutique.domain.orders.enums import OrderStatus


class OrderItem(ValueObject):
    product_id: ProductID
    unit_price: Money
    freight: Money
    quantity: int = 1

    @model_validator(mode="after")
    def validate_item(self) -> "OrderItem":
        if self.quantity <= 0:
            raise ValueError("Order-item quantity must be positive")
        if self.unit_price.currency != self.freight.currency:
            raise ValueError("Item price and freight must use the same currency")
        return self

    @property
    def total(self) -> Money:
        product_total = Money(
            amount=self.unit_price.amount * self.quantity,
            currency=self.unit_price.currency,
        )
        return product_total.add(other=self.freight)


class Order(DomainModel):
    """Order aggregate root. All item and state invariants live here."""

    id: OrderID
    customer_id: CustomerID
    purchased_at: datetime
    status: OrderStatus = OrderStatus.PENDING
    delivered_at: datetime | None = None
    items: tuple[OrderItem, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_state(self) -> "Order":
        if self.delivered_at is not None and self.delivered_at < self.purchased_at:
            raise ValueError("Delivery cannot happen before purchase")
        if self.status is OrderStatus.DELIVERED and self.delivered_at is None:
            raise ValueError("A delivered order must have a delivery timestamp")
        if len({item.unit_price.currency for item in self.items}) > 1:
            raise ValueError("All order items must use the same currency")
        return self

    @property
    def total(self) -> Money:
        if not self.items:
            return Money.zero()
        total = self.items[0].total
        for item in self.items[1:]:
            total = total.add(other=item.total)
        return total

    def add_item(self, *, item: OrderItem) -> None:
        if self.status in {OrderStatus.DELIVERED, OrderStatus.CANCELED}:
            raise DomainValidationError("Cannot modify a delivered or canceled order")
        self.items = (*self.items, item)

    def mark_delivered(self, *, delivered_at: datetime) -> None:
        if self.status is OrderStatus.CANCELED:
            raise DomainValidationError("A canceled order cannot be delivered")
        self.delivered_at = delivered_at
        self.status = OrderStatus.DELIVERED
