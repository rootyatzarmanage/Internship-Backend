"""control panel slug/value columns, id counters, prefixed ID columns

Revision ID: c0a1d2e3f401
Revises:
Create Date: 2026-10-26 17:20:00
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "c0a1d2e3f401"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)

ID_COLUMNS = [
    ("pim_workspaces", "workspace_id"),
    ("aim_workspaces", "workspace_id"),
    ("pim_projects", "project_id"),
    ("aim_projects", "project_id"),
    ("users", "user_id"),
    ("orders", "invoice_id"),
    ("subscription_plans", "offering_id"),
    ("tickets", "ticket_id"),
]


def _insp():
    return sa.inspect(op.get_bind())


def _has_table(table: str) -> bool:
    return _insp().has_table(table)


def _has_col(table: str, col: str) -> bool:
    return any(c["name"] == col for c in _insp().get_columns(table))


def _has_unique(table: str, col: str) -> bool:
    insp = _insp()
    for ix in insp.get_indexes(table):
        if ix.get("unique") and ix["column_names"] == [col]:
            return True
    for uc in insp.get_unique_constraints(table):
        if uc["column_names"] == [col]:
            return True
    return False


def upgrade() -> None:
    if not _has_table("ControlPanel"):
        op.create_table(
            "ControlPanel",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("slug", sa.Text, nullable=False),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("name_prefix", sa.Text, nullable=True),
            sa.Column("value", sa.Text, nullable=True),
            sa.Column("value_json", postgresql.JSONB, nullable=True),
            sa.Column("fieldtype", sa.Integer, nullable=False),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
            sa.Column("deleted_at", TS, nullable=True),
        )
        op.create_index("ix_ControlPanel_slug", "ControlPanel", ["slug"], unique=True)
    else:
        if not _has_col("ControlPanel", "value"):
            op.add_column("ControlPanel", sa.Column("value", sa.Text, nullable=True))
        if not _has_col("ControlPanel", "value_json"):
            op.add_column("ControlPanel", sa.Column("value_json", postgresql.JSONB, nullable=True))
        if not _has_col("ControlPanel", "slug"):
            op.add_column("ControlPanel", sa.Column("slug", sa.Text, nullable=True))
            op.execute("""UPDATE "ControlPanel" SET slug = 'Legacy/' || id::text WHERE slug IS NULL""")
            op.alter_column("ControlPanel", "slug", existing_type=sa.Text, nullable=False)
        if not _has_unique("ControlPanel", "slug"):
            op.create_index("ix_ControlPanel_slug", "ControlPanel", ["slug"], unique=True)


    if not _has_table("id_counters"):
        op.create_table(
            "id_counters",
            sa.Column("slug", sa.Text, primary_key=True),
            sa.Column("last_number", sa.Integer, nullable=False),
        )

    if not _has_table("contact_information"):
        op.create_table(
            "contact_information",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("contact_id", sa.Text, nullable=True),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("email", sa.Text, nullable=False),
            sa.Column("phone", sa.Text, nullable=True),
            sa.Column("subject", sa.Text, nullable=True),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("status", sa.Text, nullable=False),
            sa.Column("deleted_at", TS, nullable=True),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
        )
        op.create_index("ix_contact_information_contact_id", "contact_information", ["contact_id"], unique=True)
        op.create_index("ix_contact_information_email", "contact_information", ["email"])

    if not _has_table("book_demos"):
        op.create_table(
            "book_demos",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("book_demo_id", sa.Text, nullable=True),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("email", sa.Text, nullable=False),
            sa.Column("phone", sa.Text, nullable=True),
            sa.Column("company", sa.Text, nullable=True),
            sa.Column("preferred_at", TS, nullable=True),
            sa.Column("message", sa.Text, nullable=True),
            sa.Column("status", sa.Text, nullable=False),
            sa.Column("deleted_at", TS, nullable=True),
            sa.Column("created_at", TS, nullable=False),
            sa.Column("updated_at", TS, nullable=False),
        )
        op.create_index("ix_book_demos_book_demo_id", "book_demos", ["book_demo_id"], unique=True)
        op.create_index("ix_book_demos_email", "book_demos", ["email"])

    for table, col in ID_COLUMNS:
        if not _has_table(table):
            continue
        if not _has_col(table, col):
            op.add_column(table, sa.Column(col, sa.Text, nullable=True))
        if not _has_unique(table, col):
            op.create_index(f"ix_{table}_{col}", table, [col], unique=True)


def downgrade() -> None:
    for table, col in reversed(ID_COLUMNS):
        if not _has_table(table) or not _has_col(table, col):
            continue
        for ix in _insp().get_indexes(table):
            if ix["column_names"] == [col]:
                op.drop_index(ix["name"], table_name=table)
        op.drop_column(table, col)

    for table in ("book_demos", "contact_information", "id_counters"):
        if _has_table(table):
            op.drop_table(table)

    if _has_table("ControlPanel"):
        for ix in _insp().get_indexes("ControlPanel"):
            if ix["column_names"] == ["slug"]:
                op.drop_index(ix["name"], table_name="ControlPanel")
        for col in ("value_json", "value", "slug"):
            if _has_col("ControlPanel", col):
                op.drop_column("ControlPanel", col)
