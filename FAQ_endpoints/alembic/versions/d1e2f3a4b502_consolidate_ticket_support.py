"""Consolidate ticket workflow and rule storage without dropping legacy data.

Revision ID: d1e2f3a4b502
Revises: c0a1d2e3f401
Create Date: 2026-10-27
"""
import json
from datetime import datetime, timezone
from uuid import uuid4

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d1e2f3a4b502"
down_revision = "c0a1d2e3f401"
branch_labels = None
depends_on = None

UUID = postgresql.UUID(as_uuid=True)
TS = sa.DateTime(timezone=True)
RULES_SLUG = "Ticket Settings/Escalation Rules"
RULE_DEFAULTS = {"auto_return": True, "notify_super_admin": True, "allow_skip_levels": False}
WORKFLOW_FIELDS = (
    "priority", "level_id", "assignee_id", "assigned_at", "due_at",
    "resolved_at", "resolved_level", "resolved_by",
)


def _has_table(name):
    return sa.inspect(op.get_bind()).has_table(name)


def _ensure_index(table, column):
    names = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}
    name = f"ix_{table}_{column}"
    if name not in names:
        op.create_index(name, table, [column])


def _support_tables():
    if not _has_table("ticket_levels"):
        op.create_table(
            "ticket_levels",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("description", sa.Text, nullable=True),
            sa.Column("sla_hours", sa.Integer, nullable=False),
            sa.Column("created_at", TS, nullable=False),
        )
    if not _has_table("ticket_team_members"):
        op.create_table(
            "ticket_team_members",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=True),
            sa.Column("name", sa.Text, nullable=False),
            sa.Column("level_id", sa.Integer, sa.ForeignKey("ticket_levels.id"), nullable=False),
            sa.Column("is_active", sa.Boolean, nullable=False),
            sa.Column("created_at", TS, nullable=False),
        )
    if not _has_table("ticket_events"):
        op.create_table(
            "ticket_events",
            sa.Column("id", UUID, primary_key=True),
            sa.Column("ticket_id", UUID, sa.ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.Text, nullable=False),
            sa.Column("text", sa.Text, nullable=False),
            sa.Column("by_name", sa.Text, nullable=False),
            sa.Column("level_id", sa.Integer, nullable=False),
            sa.Column("created_at", TS, nullable=False),
        )
    for table, column in (
        ("ticket_team_members", "level_id"),
        ("ticket_events", "ticket_id"),
        ("ticket_events", "created_at"),
    ):
        _ensure_index(table, column)


def _workflow_columns(on_ticket=False):
    return [
        sa.Column("priority", sa.Text, nullable=False, server_default="medium" if on_ticket else None),
        sa.Column("level_id", sa.Integer, nullable=False, server_default="0" if on_ticket else None),
        sa.Column(
            "assignee_id", UUID,
            sa.ForeignKey("ticket_team_members.id", name="fk_tickets_assignee_id_ticket_team_members" if on_ticket else None),
            nullable=True,
        ),
        sa.Column("assigned_at", TS, nullable=True),
        sa.Column("due_at", TS, nullable=True),
        sa.Column("resolved_at", TS, nullable=True),
        sa.Column("resolved_level", sa.Integer, nullable=True),
        sa.Column(
            "resolved_by", UUID,
            sa.ForeignKey("ticket_team_members.id", name="fk_tickets_resolved_by_ticket_team_members" if on_ticket else None),
            nullable=True,
        ),
    ]


def _copy_workflows(existing_columns):
    if not _has_table("ticket_workflows"):
        return
    connection = op.get_bind()
    compare = [field for field in WORKFLOW_FIELDS if field in existing_columns]
    if compare:
        differences = " OR ".join(f"t.{field} IS DISTINCT FROM w.{field}" for field in compare)
        conflict = connection.execute(sa.text(
            "SELECT t.id FROM tickets t JOIN ticket_workflows w ON w.ticket_id = t.id "
            f"WHERE {differences} LIMIT 1"
        )).first()
        if conflict:
            raise RuntimeError("Ticket and legacy workflow values conflict; resolve before migrating")
    assignments = ", ".join(f"{field} = w.{field}" for field in WORKFLOW_FIELDS)
    connection.execute(sa.text(
        f"UPDATE tickets AS t SET {assignments} FROM ticket_workflows AS w WHERE w.ticket_id = t.id"
    ))
    differences = " OR ".join(f"t.{field} IS DISTINCT FROM w.{field}" for field in WORKFLOW_FIELDS)
    mismatch = connection.execute(sa.text(
        "SELECT w.ticket_id FROM ticket_workflows w LEFT JOIN tickets t ON t.id = w.ticket_id "
        f"WHERE t.id IS NULL OR {differences} LIMIT 1"
    )).first()
    if mismatch:
        raise RuntimeError("Legacy workflow transfer did not preserve every row")


def _copy_rules():
    if not _has_table("ticket_rule_settings"):
        return
    connection = op.get_bind()
    legacy = connection.execute(sa.text(
        "SELECT auto_return, notify_super_admin, allow_skip_levels FROM ticket_rule_settings WHERE id = 1"
    )).mappings().first()
    if not legacy:
        return
    values = {name: bool(legacy[name]) for name in RULE_DEFAULTS}
    current = connection.execute(sa.text(
        'SELECT value_json, deleted_at FROM "ControlPanel" WHERE slug = :slug'
    ), {"slug": RULES_SLUG}).mappings().first()
    if current:
        current_values = current["value_json"] or {}
        if isinstance(current_values, str):
            current_values = json.loads(current_values)
        effective = {**RULE_DEFAULTS, **current_values}
        if current["deleted_at"] is not None or any(effective[key] != value for key, value in values.items()):
            raise RuntimeError("Ticket rule configuration conflicts with legacy rules; resolve before migrating")
        return
    now = datetime.now(timezone.utc)
    connection.execute(sa.text(
        'INSERT INTO "ControlPanel" '
        '(id, slug, name, fieldtype, value_json, created_at, updated_at) '
        'VALUES (:id, :slug, :name, 2, CAST(:rules AS jsonb), :now, :now)'
    ), {
        "id": uuid4(), "slug": RULES_SLUG, "name": "Ticket escalation rules",
        "rules": json.dumps(values), "now": now,
    })


def upgrade():
    if not _has_table("tickets") or not _has_table("users") or not _has_table("ControlPanel"):
        raise RuntimeError("Apply the existing application schema and c0a1d2e3f401 before ticket support")
    existing_columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("tickets")}
    _support_tables()
    for column in _workflow_columns(on_ticket=True):
        if column.name not in existing_columns:
            op.add_column("tickets", column)
    for column in ("level_id", "assignee_id", "due_at", "resolved_at"):
        _ensure_index("tickets", column)
    _copy_workflows(existing_columns)
    _copy_rules()
    # Effective SLA for existing active tickets, including legacy pending rows.
    op.execute(sa.text(
        "UPDATE tickets SET due_at = created_at + INTERVAL '2 hours' "
        "WHERE due_at IS NULL AND status IN "
        "('pending', 'open', 'on_going', 'escalation_pending', 'needs_super_admin')"
    ))
    # Old workflow/rule tables, when present, are intentionally retained as
    # rollback data. They are not mapped or queried by the application.


def downgrade():
    # Restore the previous five-table layout before removing ticket columns.
    # Keep levels, members and events: dropping them would destroy support data.
    if not _has_table("ticket_workflows"):
        op.create_table(
            "ticket_workflows",
            sa.Column("ticket_id", UUID, sa.ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
            *_workflow_columns(),
        )
    for column in ("level_id", "assignee_id", "due_at", "resolved_at"):
        _ensure_index("ticket_workflows", column)
    fields = ", ".join(WORKFLOW_FIELDS)
    updates = ", ".join(f"{field} = EXCLUDED.{field}" for field in WORKFLOW_FIELDS)
    op.execute(sa.text(
        f"INSERT INTO ticket_workflows (ticket_id, {fields}) SELECT id, {fields} FROM tickets "
        f"ON CONFLICT (ticket_id) DO UPDATE SET {updates}"
    ))
    if not _has_table("ticket_rule_settings"):
        op.create_table(
            "ticket_rule_settings",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("auto_return", sa.Boolean, nullable=False),
            sa.Column("notify_super_admin", sa.Boolean, nullable=False),
            sa.Column("allow_skip_levels", sa.Boolean, nullable=False),
        )
    connection = op.get_bind()
    row = connection.execute(sa.text(
        'SELECT value_json FROM "ControlPanel" WHERE slug = :slug AND deleted_at IS NULL'
    ), {"slug": RULES_SLUG}).first()
    values = row[0] if row else {}
    if isinstance(values, str):
        values = json.loads(values)
    values = {**RULE_DEFAULTS, **(values or {})}
    connection.execute(sa.text(
        "INSERT INTO ticket_rule_settings (id, auto_return, notify_super_admin, allow_skip_levels) "
        "VALUES (1, :auto_return, :notify_super_admin, :allow_skip_levels) "
        "ON CONFLICT (id) DO UPDATE SET auto_return = EXCLUDED.auto_return, "
        "notify_super_admin = EXCLUDED.notify_super_admin, allow_skip_levels = EXCLUDED.allow_skip_levels"
    ), {key: values[key] for key in RULE_DEFAULTS})
    for field in reversed(WORKFLOW_FIELDS):
        op.drop_column("tickets", field)
