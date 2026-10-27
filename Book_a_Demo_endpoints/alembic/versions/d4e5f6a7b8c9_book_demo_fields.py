"""book_demos: job_role, visitor_timezone, consent + preferred_at index

Revision ID: d4e5f6a7b8c9
Revises: c0a1d2e3f401
Create Date: 2026-10-27 10:00:00
"""
import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
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
    if not _has_col("job_role"):
        op.add_column(TABLE, sa.Column("job_role", sa.Text, nullable=True))
    if not _has_col("visitor_timezone"):
        op.add_column(TABLE, sa.Column("visitor_timezone", sa.Text, nullable=True))
    if not _has_col("consent"):
        op.add_column(TABLE, sa.Column("consent", sa.Boolean, nullable=False, server_default=sa.false()))
    if not _has_index("ix_book_demos_preferred_at"):
        op.create_index("ix_book_demos_preferred_at", TABLE, ["preferred_at"])


def downgrade() -> None:
    if not _insp().has_table(TABLE):
        return
    if _has_index("ix_book_demos_preferred_at"):
        op.drop_index("ix_book_demos_preferred_at", table_name=TABLE)
    for col in ("consent", "visitor_timezone", "job_role"):
        if _has_col(col):
            op.drop_column(TABLE, col)
