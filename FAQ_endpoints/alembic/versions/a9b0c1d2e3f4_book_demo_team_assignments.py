"""book demo team (single table) and booking assignment columns

Revision ID: a9b0c1d2e3f4
Revises: f8b9c0d1e2f3
Create Date: 2026-10-30 10:00:00
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "a9b0c1d2e3f4"
down_revision = "f8b9c0d1e2f3"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_index(table: str, name: str) -> bool:
    return any(ix["name"] == name for ix in _insp().get_indexes(table))


def _has_column(table: str, name: str) -> bool:
    return any(c["name"] == name for c in _insp().get_columns(table))


def upgrade() -> None:
    # main.py runs Base.metadata.create_all on startup, so the new table may already exist.
    # create_all never adds columns to an existing table, so book_demos is always altered here.
    if not _has_table("book_demo_team"):
        op.create_table(
            "book_demo_team",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("kind", sa.Text, nullable=False),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("email", sa.Text, nullable=True),
            sa.Column("role", sa.Text, nullable=True),
            sa.Column("parent_id", UUID, sa.ForeignKey("book_demo_team.id", ondelete="RESTRICT"), nullable=True),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
            sa.Column("created_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_by", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.CheckConstraint("kind in ('level', 'member')", name="ck_book_demo_team_kind"),
            sa.CheckConstraint(
                "(kind = 'level' and parent_id is null) or "
                "(kind = 'member' and parent_id is not null and email is not null and role is not null)",
                name="ck_book_demo_team_shape"),
        )
    if not _has_index("book_demo_team", "ix_book_demo_team_kind"):
        op.create_index("ix_book_demo_team_kind", "book_demo_team", ["kind"])
    if not _has_index("book_demo_team", "ix_book_demo_team_parent_id"):
        op.create_index("ix_book_demo_team_parent_id", "book_demo_team", ["parent_id"])
    if not _has_index("book_demo_team", "uq_book_demo_team_level_name"):
        op.create_index("uq_book_demo_team_level_name", "book_demo_team", [sa.text("lower(name)")],
                        unique=True, postgresql_where=sa.text("kind = 'level'"))
    if not _has_index("book_demo_team", "uq_book_demo_team_member_email"):
        op.create_index("uq_book_demo_team_member_email", "book_demo_team", [sa.text("lower(email)")],
                        unique=True, postgresql_where=sa.text("kind = 'member'"))

    columns = {
        "assigned_member_ids": sa.Column("assigned_member_ids", postgresql.ARRAY(UUID), nullable=False,
                                         server_default=sa.text("'{}'::uuid[]")),
        "assigned_primary_id": sa.Column("assigned_primary_id", UUID, nullable=True),
        "assignment_note": sa.Column("assignment_note", sa.Text, nullable=True),
        "assignment_history": sa.Column("assignment_history", postgresql.JSONB, nullable=False,
                                        server_default=sa.text("'[]'::jsonb")),
        "assignment_updated_at": sa.Column("assignment_updated_at", TS, nullable=True),
        "assignment_updated_by": sa.Column("assignment_updated_by", UUID, sa.ForeignKey("users.id"), nullable=True),
    }
    for name, column in columns.items():
        if not _has_column("book_demos", name):
            op.add_column("book_demos", column)


def downgrade() -> None:
    for name in ("assignment_updated_by", "assignment_updated_at", "assignment_history",
                 "assignment_note", "assigned_primary_id", "assigned_member_ids"):
        if _has_column("book_demos", name):
            op.drop_column("book_demos", name)
    if _has_table("book_demo_team"):
        op.drop_table("book_demo_team")
