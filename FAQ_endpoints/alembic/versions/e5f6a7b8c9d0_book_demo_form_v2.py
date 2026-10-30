"""book_demos: phone_code, country, description, opt; drop job_role, consent

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-27 17:30:00
"""
import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

TABLE = "book_demos"


def _has_col(col: str) -> bool:
    return any(c["name"] == col for c in sa.inspect(op.get_bind()).get_columns(TABLE))


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table(TABLE):
        return
    for col in ("phone_code", "country", "description"):
        if not _has_col(col):
            op.add_column(TABLE, sa.Column(col, sa.Text, nullable=True))
    if not _has_col("opt"):
        op.add_column(TABLE, sa.Column("opt", sa.SmallInteger, nullable=False, server_default="1"))
    for col in ("job_role", "consent"):
        if _has_col(col):
            op.drop_column(TABLE, col)


def downgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table(TABLE):
        return
    if not _has_col("job_role"):
        op.add_column(TABLE, sa.Column("job_role", sa.Text, nullable=True))
    if not _has_col("consent"):
        op.add_column(TABLE, sa.Column("consent", sa.Boolean, nullable=False, server_default=sa.false()))
    for col in ("opt", "description", "country", "phone_code"):
        if _has_col(col):
            op.drop_column(TABLE, col)
