"""Medication model — prescriptions and medication tracking."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text
from app.models.base import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Medication(db.Model):
    """Patient medication / prescription record.

    Discontinuation is a soft-delete: status is set to 'discontinued',
    the record is never hard-deleted.
    """

    __tablename__ = "medications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'discontinued', 'on_hold')",
            name="ck_medications_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    route: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prescribed_by: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=True, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    side_effects: Mapped[str | None] = mapped_column(Text, nullable=True)
    refills_remaining: Mapped[int] = mapped_column(Integer, default=0)
    pharmacy_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    patient = relationship("User", foreign_keys=[patient_id])
    prescriber = relationship("User", foreign_keys=[prescribed_by])

    def __repr__(self) -> str:
        return f"<Medication {self.name} {self.dosage} ({self.status})>"
