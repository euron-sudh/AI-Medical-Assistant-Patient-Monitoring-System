"""Idempotent repairs when persisted DB schema lags behind SQLAlchemy models.

``db.create_all()`` creates missing tables but does not update CHECK constraints
on existing tables; Docker volumes can keep an old ``ck_appointments_status``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import text

if TYPE_CHECKING:
    from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)


def repair_appointments_status_check_constraint(db: "SQLAlchemy") -> None:
    """PostgreSQL only: replace appointments status CHECK with model-allowed values."""
    bind = db.engine
    if bind.dialect.name != "postgresql":
        return
    try:
        with bind.begin() as conn:
            conn.execute(text("ALTER TABLE appointments DROP CONSTRAINT IF EXISTS ck_appointments_status"))
            conn.execute(
                text(
                    "ALTER TABLE appointments ADD CONSTRAINT ck_appointments_status "
                    "CHECK (status IN ("
                    "'pending', 'scheduled', 'confirmed', 'in_progress', "
                    "'completed', 'cancelled', 'no_show', 'denied'))"
                )
            )
        logger.info("appointments_status_check_constraint repaired for current model")
    except Exception as exc:
        logger.warning("repair_appointments_status_check_constraint skipped: %s", exc)
