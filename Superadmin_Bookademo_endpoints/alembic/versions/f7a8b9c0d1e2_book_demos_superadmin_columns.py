"""book_demos: phone_code, country, description, opt, visitor_timezone + preferred_at index

Revision ID: f7a8b9c0d1e2
Revises: c0a1d2e3f401
Create Date: 2026-10-29 16:00:00
"""
import sqlalchemy as sa
from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "c0a1d2e3f401"
branch_labels = None
depends_on = None

TABLE = "book_demos"


def _insp():
    return sa.inspect(op.get_bind())


def _has_col(col: str) -> bool:
    return any(c["name"] == col for c in _insp().get_columns(TABLE))


def _has_index(name: str) -> bool:
    return any(ix["name"] == name for ix in _insp().get_indexes(TABLE))


def upgrade() -> None:
    if not _insp().has_table(TABLE):
        return
    for col in ("phone_code", "country", "description", "visitor_timezone"):
        if not _has_col(col):
            op.add_column(TABLE, sa.Column(col, sa.Text, nullable=True))
    if not _has_col("opt"):
        op.add_column(TABLE, sa.Column("opt", sa.SmallInteger, nullable=False, server_default="1"))
    if not _has_index("ix_book_demos_preferred_at"):
        op.create_index("ix_book_demos_preferred_at", TABLE, ["preferred_at"])


def downgrade() -> None:
    if not _insp().has_table(TABLE):
        return
    if _has_index("ix_book_demos_preferred_at"):
        op.drop_index("ix_book_demos_preferred_at", table_name=TABLE)
    for col in ("opt", "visitor_timezone", "description", "country", "phone_code"):
        if _has_col(col):
            op.drop_column(TABLE, col)
