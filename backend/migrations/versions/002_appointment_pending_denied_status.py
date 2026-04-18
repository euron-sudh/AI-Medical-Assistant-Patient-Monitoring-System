"""Allow appointment statuses pending and denied on PostgreSQL.

Revision ID: 002_appt_status
Revises: 001_initial
Create Date: 2026-04-17

Replaces ``ck_appointments_status`` when an older DB (or SQLAlchemy create_all)
still has a CHECK that omits ``pending`` / ``denied``.
"""

from alembic import op
from sqlalchemy import text

revision = "002_appt_status"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(text("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS ck_appointments_status"))
    op.execute(
        text(
            "ALTER TABLE appointments ADD CONSTRAINT ck_appointments_status "
            "CHECK (status IN ("
            "'pending', 'scheduled', 'confirmed', 'in_progress', "
            "'completed', 'cancelled', 'no_show', 'denied'))"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(text("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS ck_appointments_status"))
    op.execute(
        text(
            "ALTER TABLE appointments ADD CONSTRAINT ck_appointments_status "
            "CHECK (status IN ("
            "'scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'))"
        )
    )
