"""add lead metadata

Revision ID: 20260708_0002
Revises: 20260708_0001
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa


revision = "20260708_0002"
down_revision = "20260708_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.alter_column("leads", "metadata", server_default=None)


def downgrade() -> None:
    op.drop_column("leads", "metadata")
