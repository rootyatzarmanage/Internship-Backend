"""create tickets tables

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = "5df22ff4a934"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS tickets_ticket_no_seq START 100001")

    op.create_table(
        "tickets",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("ticket_no", sa.Integer, nullable=False),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("category", sa.Text, nullable=False),
        sa.Column("subject", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("deleted_at", TS, nullable=True),
        sa.Column("deleted_by", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", TS, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", UUID, nullable=True),
    )
    op.create_index("ix_tickets_ticket_no", "tickets", ["ticket_no"], unique=True)
    op.create_index("ix_tickets_user_id", "tickets", ["user_id"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    op.create_table(
        "ticket_projects",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("ticket_id", UUID, sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", UUID, nullable=False),
        sa.Column("product_type", sa.Text, nullable=False),
        sa.Column("project_name", sa.Text, nullable=False),
        sa.Column("workspace_name", sa.Text, nullable=True),
        sa.Column("thumbnail_url", sa.Text, nullable=True),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_projects_ticket_id", "ticket_projects", ["ticket_id"])
    op.create_index("ix_ticket_projects_project_id", "ticket_projects", ["project_id"])

    op.create_table(
        "ticket_replies",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("ticket_id", UUID, sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_role", sa.Text, nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_replies_ticket_id", "ticket_replies", ["ticket_id"])

    op.create_table(
        "ticket_attachments",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("ticket_id", UUID, sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reply_id", UUID, sa.ForeignKey("ticket_replies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("file_name", sa.Text, nullable=False),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("file_url", sa.Text, nullable=False),
        sa.Column("content_type", sa.Text, nullable=True),
        sa.Column("size_bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("uploaded_by", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", TS, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_ticket_attachments_ticket_id", "ticket_attachments", ["ticket_id"])
    op.create_index("ix_ticket_attachments_reply_id", "ticket_attachments", ["reply_id"])


def downgrade() -> None:
    op.drop_table("ticket_attachments")
    op.drop_table("ticket_replies")
    op.drop_table("ticket_projects")
    op.drop_table("tickets")
    op.execute("DROP SEQUENCE IF EXISTS tickets_ticket_no_seq")