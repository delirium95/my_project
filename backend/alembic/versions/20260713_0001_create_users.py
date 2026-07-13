"""create initial boutique schema

Revision ID: 20260713_0001
Revises:
Create Date: 2026-07-13 16:20:00

"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260713_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auth_subject", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=True),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("auth_subject"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_auth_subject"), "users", ["auth_subject"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_table(
        "customers",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_state"), "customers", ["state"], unique=False)
    op.create_table(
        "products",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_table(
        "orders",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("purchased_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_customer_id"), "orders", ["customer_id"], unique=False)
    op.create_index(op.f("ix_orders_purchased_at"), "orders", ["purchased_at"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index("ix_orders_status_purchased_at", "orders", ["status", "purchased_at"], unique=False)
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.String(length=64), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("freight_value", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", "line_number"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_order_items_product_id"), table_name="order_items")
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("ix_orders_status_purchased_at", table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_purchased_at"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_id"), table_name="orders")
    op.drop_table("orders")
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_table("products")
    op.drop_index(op.f("ix_customers_state"), table_name="customers")
    op.drop_table("customers")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_auth_subject"), table_name="users")
    op.drop_table("users")
