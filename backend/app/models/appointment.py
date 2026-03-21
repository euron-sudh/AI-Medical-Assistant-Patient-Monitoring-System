"""Appointment model — scheduling and status management for patient visits."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableUUID


class Appointment(db.Model):
    """Patient appointment with a doctor.

    Supports in-person, telemedicine, follow-up, and emergency appointment types.
    Tracks full lifecycle from scheduled through completion or cancellation.
    """

    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint(
            "appointment_type IN ('in_person', 'telemedicine', 'follow_up', 'emergency')",
            name="ck_appointments_type",
        ),
        CheckConstraint(
            "status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show')",
            name="ck_appointments_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    appointment_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="in_person"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="scheduled", index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=True
    )
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="patient_appointments")
    doctor = relationship("User", foreign_keys=[doctor_id], backref="doctor_appointments")
    telemedicine_session = relationship(
        "TelemedicineSession", back_populates="appointment", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment {self.id} patient={self.patient_id} "
            f"doctor={self.doctor_id} status={self.status}>"
        )
