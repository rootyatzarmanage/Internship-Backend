"""Add audit fields to ticket support tables.

Revision ID: e2f3a4b5c603
Revises: d1e2f3a4b502
Create Date: 2026-10-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e2f3a4b5c603"
down_revision = "d1e2f3a4b502"
branch_labels = None
depends_on = None

TABLES = ("ticket_levels", "ticket_team_members", "ticket_events")


def upgrade():
    for table in TABLES:
        op.add_column(table, sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        for column in ("created_by", "updated_by"):
            op.add_column(table, sa.Column(column, postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(f"fk_{table}_{column}_users", table, "users", [column], ["id"])
        op.execute(sa.text(f"UPDATE {table} SET updated_at = created_at"))
        op.alter_column(table, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=False)


def downgrade():
    for table in reversed(TABLES):
        for column in ("updated_by", "created_by"):
            op.drop_constraint(f"fk_{table}_{column}_users", table, type_="foreignkey")
            op.drop_column(table, column)
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "updated_at")
