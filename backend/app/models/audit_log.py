"""AuditLog model — immutable, append-only HIPAA compliance log.

This table records every access to Protected Health Information (PHI).
Audit logs are NEVER updated or deleted — they are immutable by design.
There is intentionally NO updated_at or deleted_at column.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import PortableUUID, PortableJSON


class AuditLog(db.Model):
    """HIPAA audit log entry — immutable record of PHI access.

    Every read, write, or export of Protected Health Information is logged here.
    Retention: minimum 6 years per HIPAA requirements.
    Access: restricted to admin role only.
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_patient_id", "patient_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), nullable=True
    )
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_method: Mapped[str | None] = mapped_column(String(10), nullable=True)
    request_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Intentionally NO updated_at — audit logs are immutable
    # Intentionally NO deleted_at — audit logs are never deleted

    def __repr__(self) -> str:
        return (
            f"<AuditLog {self.action} on {self.resource_type} "
            f"by user={self.user_id} at {self.created_at}>"
        )
