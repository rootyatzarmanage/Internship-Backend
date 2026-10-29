import sqlalchemy as sa
from alembic import op

revision = "d1e2f3a4b501"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None

TABLE = "contact_information"


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table(TABLE):
        return 
    cols = {c["name"] for c in insp.get_columns(TABLE)}

    if "first_name" not in cols:
        op.add_column(TABLE, sa.Column("first_name", sa.Text, nullable=True))
    if "last_name" not in cols:
        op.add_column(TABLE, sa.Column("last_name", sa.Text, nullable=True))
    if "phone_country_code" not in cols:
        op.add_column(TABLE, sa.Column("phone_country_code", sa.Text, nullable=True))
    if "interested_in" not in cols:
        op.add_column(TABLE, sa.Column("interested_in", sa.Text, nullable=True))
        op.create_index("ix_contact_information_interested_in", TABLE, ["interested_in"])

    if "name" in cols:
        op.execute(f"""
            UPDATE {TABLE}
            SET first_name = split_part(trim(name), ' ', 1),
                last_name  = NULLIF(trim(substr(trim(name), length(split_part(trim(name), ' ', 1)) + 1)), '')
            WHERE first_name IS NULL
        """)
    op.execute(f"UPDATE {TABLE} SET first_name = '' WHERE first_name IS NULL")
    op.alter_column(TABLE, "first_name", existing_type=sa.Text, nullable=False)

    if "name" in cols:
        op.drop_column(TABLE, "name")
    if "subject" in cols:
        op.drop_column(TABLE, "subject")


def downgrade() -> None:
    op.add_column(TABLE, sa.Column("name", sa.Text, nullable=True))
    op.add_column(TABLE, sa.Column("subject", sa.Text, nullable=True))
    op.execute(f"UPDATE {TABLE} SET name = trim(first_name || ' ' || coalesce(last_name, ''))")
    op.alter_column(TABLE, "name", existing_type=sa.Text, nullable=False)
    op.drop_index("ix_contact_information_interested_in", table_name=TABLE)
    for c in ("interested_in", "phone_country_code", "last_name", "first_name"):
        op.drop_column(TABLE, c)