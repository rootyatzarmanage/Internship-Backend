"""create notifications table (super admin notifications, one row per super admin)

Revision ID: d4e5f6a7b801
Revises: d1e2f3a4b501
Create Date: 2026-10-29 10:00:00
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d4e5f6a7b801"
down_revision = "d1e2f3a4b501"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)

INDEXES = [
    ("ix_notifications_user_id", ["user_id"]),
    ("ix_notifications_category_id", ["category_id"]),
    ("ix_notifications_created_at", ["created_at"]),
    ("ix_notifications_user_unread", ["user_id", "is_read"]),
]


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_index(table: str, name: str) -> bool:
    return any(ix["name"] == name for ix in _insp().get_indexes(table))


def upgrade() -> None:
    # main.py runs Base.metadata.create_all on startup, so the table may already exist.
    if not _has_table("notifications"):
        op.create_table(
            "notifications",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("notification_type", sa.Text, nullable=False),
            sa.Column("category_id", UUID, nullable=False),
            sa.Column("platform_id", UUID, nullable=True),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("resource_id", UUID, nullable=True),
            sa.Column("is_read", sa.SmallInteger, nullable=False, server_default="0"),
            sa.Column("read_at", TS, nullable=True),
            sa.Column("deleted_at", TS, nullable=True),
            sa.Column("deleted_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
            sa.Column("updated_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.CheckConstraint("is_read IN (0, 1)", name="ck_notifications_is_read"),
        )

    for name, cols in INDEXES:
        if not _has_index("notifications", name):
            op.create_index(name, "notifications", cols)


def downgrade() -> None:
    if not _has_table("notifications"):
        return
    for name, _ in reversed(INDEXES):
        if _has_index("notifications", name):
            op.drop_index(name, table_name="notifications")
    op.drop_table("notifications")
