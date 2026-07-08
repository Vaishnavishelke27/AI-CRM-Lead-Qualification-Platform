"""growth features

Revision ID: 20260708_0003
Revises: 20260708_0002
Create Date: 2026-07-08
"""
from alembic import op
import sqlalchemy as sa


revision = "20260708_0003"
down_revision = "20260708_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("assigned_to", sa.String(length=255), nullable=True))
    op.add_column("emails", sa.Column("tracking_token", sa.String(length=255), nullable=True))
    op.add_column("emails", sa.Column("opened_at", sa.DateTime(), nullable=True))
    op.add_column("emails", sa.Column("clicked_at", sa.DateTime(), nullable=True))
    op.add_column("emails", sa.Column("open_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("emails", sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"))
    op.create_index(op.f("ix_emails_tracking_token"), "emails", ["tracking_token"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_emails_tracking_token"), table_name="emails")
    op.drop_column("emails", "click_count")
    op.drop_column("emails", "open_count")
    op.drop_column("emails", "clicked_at")
    op.drop_column("emails", "opened_at")
    op.drop_column("emails", "tracking_token")
    op.drop_column("leads", "assigned_to")
