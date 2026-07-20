"""use timezone-aware timestamps

Revision ID: 20260717_0004
Revises: 20260708_0003
Create Date: 2026-07-17
"""

from alembic import op
import sqlalchemy as sa


revision = "20260717_0004"
down_revision = "20260708_0003"
branch_labels = None
depends_on = None


TIMESTAMP_COLUMNS = {
    "leads": ("created_at",),
    "tasks": ("due_date",),
    "emails": ("sent_at", "opened_at", "clicked_at"),
    "users": ("created_at",),
}


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table, columns in TIMESTAMP_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return

    for table, columns in TIMESTAMP_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
