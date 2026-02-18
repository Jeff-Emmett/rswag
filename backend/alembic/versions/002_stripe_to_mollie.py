"""Migrate from Stripe to Mollie payment provider

Revision ID: 002_stripe_to_mollie
Revises: 001_initial
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_stripe_to_mollie"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename Stripe-specific columns to generic payment columns
    op.alter_column("orders", "stripe_session_id", new_column_name="payment_id")
    op.alter_column("orders", "stripe_payment_intent_id", new_column_name="payment_method")

    # Add payment_provider column
    op.add_column("orders", sa.Column("payment_provider", sa.String(50), nullable=True))

    # Rename stripe_customer_id on customers table
    op.alter_column("customers", "stripe_customer_id", new_column_name="external_id")


def downgrade() -> None:
    op.alter_column("customers", "external_id", new_column_name="stripe_customer_id")
    op.drop_column("orders", "payment_provider")
    op.alter_column("orders", "payment_method", new_column_name="stripe_payment_intent_id")
    op.alter_column("orders", "payment_id", new_column_name="stripe_session_id")
