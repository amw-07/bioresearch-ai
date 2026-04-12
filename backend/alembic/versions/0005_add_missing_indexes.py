"""Skip migration — indexes referenced deleted tables.

This revision existed to add indexes to usage_events and team_invitations.
Both tables were deleted in the Week 1 cleanup. This file is kept as a
no-op placeholder to maintain the migration chain integrity.

Revision ID: 0005_indexes
Revises:     0003_phase23
"""

from alembic import op

revision = "0005_indexes"
down_revision = "0003_phase23"   # ← FIXED: was "0004_phase24" (deleted)
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: usage_events and team_invitations tables were deleted in
    # the Week 1 BioResearch AI conversion. Original indexes are gone.
    pass


def downgrade() -> None:
    pass