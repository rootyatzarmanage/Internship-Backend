"""create faqs table

Revision ID: b1c2d3e4f5a6
Revises: a9b0c1d2e3f4
Create Date: 2026-10-30 10:00:00
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f5a6"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)

INDEXES = [
    ("ix_faqs_display_order", ["display_order"]),
    ("ix_faqs_is_active", ["is_active"]),
    ("ix_faqs_created_at", ["created_at"]),
]


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_index(table: str, name: str) -> bool:
    return any(ix["name"] == name for ix in _insp().get_indexes(table))


def upgrade() -> None:
    if not _has_table("faqs"):
        op.create_table(
            "faqs",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("question", sa.Text, nullable=False),
            sa.Column("answer", sa.Text, nullable=False),
            sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
            sa.Column("is_active", sa.SmallInteger, nullable=False, server_default="1"),
            sa.Column("created_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("deleted_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
            sa.Column("deleted_at", TS, nullable=True),
            sa.CheckConstraint("is_active IN (0, 1)", name="ck_faqs_is_active"),
        )

    for name, cols in INDEXES:
        if not _has_index("faqs", name):
            op.create_index(name, "faqs", cols)


def downgrade() -> None:
    if not _has_table("faqs"):
        return
    for name, _ in reversed(INDEXES):
        if _has_index("faqs", name):
            op.drop_index(name, table_name="faqs")
    op.drop_table("faqs")
