import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "b1c2d3e4f501"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB()
TS = sa.DateTime(timezone=True)


def _insp():
    return sa.inspect(op.get_bind())


def upgrade() -> None:
    if _insp().has_table("superadmin_pricing"):
        return
    op.create_table(
        "superadmin_pricing",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("currency", sa.Text, nullable=False),
        sa.Column("currency_code", sa.Text, nullable=False),
        sa.Column("active_tab_id", sa.Text, nullable=True),
        sa.Column("theme", sa.Text, nullable=False),
        sa.Column("tabs", JSONB, nullable=False),
        sa.Column("features", JSONB, nullable=False),
        sa.Column("plans", JSONB, nullable=False),
        sa.Column("created_at", TS, nullable=False),
        sa.Column("updated_at", TS, nullable=False),
        sa.Column("created_by", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_by", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("deleted_at", TS, nullable=True),
    )
    op.create_index("ix_superadmin_pricing_slug", "superadmin_pricing", ["slug"], unique=True)


def downgrade() -> None:
    if not _insp().has_table("superadmin_pricing"):
        return
    op.drop_index("ix_superadmin_pricing_slug", table_name="superadmin_pricing")
    op.drop_table("superadmin_pricing")
