"""Drop subscription and billing columns from users table.

These columns were removed from the User model during the Week 1 BioResearch AI
conversion from a SaaS billing tool to a research intelligence platform.
This migration syncs the live Supabase schema with the current model.

Revision ID: 0011
Revises: 0010
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


def _has_column(bind, table_name: str, column_name: str) -> bool:
    try:
        cols = {col["name"] for col in inspect(bind).get_columns(table_name)}
        return column_name in cols
    except Exception:
        return False


def _has_table(bind, table_name: str) -> bool:
    try:
        return table_name in inspect(bind).get_table_names()
    except Exception:
        return False


revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

# All columns to remove from users table
COLUMNS_TO_DROP = [
    "subscription_tier",
    "stripe_customer_id",
    "stripe_subscription_id",
    "stripe_price_id",
    "stripe_subscription_status",
    "subscription_period_end",
]


def upgrade() -> None:
    bind = op.get_bind()

    if not _has_table(bind, "users"):
        return

    # Drop constraints first (safe if they don't exist)
    for stmt in [
        "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_subscription_tier_check",
        "ALTER TABLE users DROP CONSTRAINT IF EXISTS users_subscription_tier_key",
        "DROP TYPE IF EXISTS subscriptiontier CASCADE",
    ]:
        try:
            bind.execute(text(stmt))
        except Exception:
            pass

    # Use raw SQL IF EXISTS — bypasses SQLAlchemy inspect caching issues
    for col in COLUMNS_TO_DROP:
        bind.execute(text(f"ALTER TABLE users DROP COLUMN IF EXISTS {col}"))
        print(f"[OK] Dropped (or skipped) users.{col}")


def downgrade() -> None:
    # Intentionally not restoring billing columns.
    # This is a one-way migration for the portfolio conversion.
    pass