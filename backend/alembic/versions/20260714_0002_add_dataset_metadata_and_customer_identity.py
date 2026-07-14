"""track dataset imports and retain Olist repeat-customer identity

Revision ID: 20260714_0002
Revises: 20260713_0001
Create Date: 2026-07-14 10:30:00

"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260714_0002"
down_revision: Union[str, Sequence[str], None] = "20260713_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("unique_id", sa.String(length=64), nullable=True))
    # Existing locally imported records did not retain this Olist field. Using the row ID keeps
    # them valid until the next explicit re-import replaces them with true unique customer IDs.
    op.execute("UPDATE customers SET unique_id = id WHERE unique_id IS NULL")
    op.alter_column("customers", "unique_id", nullable=False)
    op.create_index(op.f("ix_customers_unique_id"), "customers", ["unique_id"], unique=False)
    op.create_table(
        "dataset_metadata",
        sa.Column("dataset_name", sa.String(length=64), nullable=False),
        sa.Column("last_imported_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("dataset_name"),
    )


def downgrade() -> None:
    op.drop_table("dataset_metadata")
    op.drop_index(op.f("ix_customers_unique_id"), table_name="customers")
    op.drop_column("customers", "unique_id")
