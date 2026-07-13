import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from boutique.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_subject: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state: Mapped[str] = mapped_column(String(2), index=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    category: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_status_purchased_at", "status", "purchased_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (UniqueConstraint("order_id", "line_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    freight_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
