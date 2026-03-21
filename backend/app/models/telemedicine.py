"""TelemedicineSession model — video consultation session management."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableUUID


class TelemedicineSession(db.Model):
    """Video consultation session linked to an appointment.

    Manages Daily.co room lifecycle, tracks session duration, and stores
    AI-generated transcripts and clinical summaries from the call.
    """

    __tablename__ = "telemedicine_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('waiting', 'in_progress', 'completed', 'failed')",
            name="ck_telemedicine_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    appointment_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("appointments.id"), nullable=False, index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    room_url: Mapped[str] = mapped_column(String(500), nullable=False)
    room_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recording_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ai_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    appointment = relationship("Appointment", back_populates="telemedicine_session")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

    def __repr__(self) -> str:
        return f"<TelemedicineSession {self.id} appointment={self.appointment_id} status={self.status}>"
