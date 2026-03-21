"""SymptomSession model — patient symptom check sessions with AI analysis."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableJSON, PortableUUID


class SymptomSession(db.Model):
    """Symptom check session tracking multi-turn AI-assisted symptom analysis.

    Records chief complaint, structured symptoms, AI analysis results,
    triage level, and the full conversation log between patient and AI agent.
    """

    __tablename__ = "symptom_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'cancelled')",
            name="ck_symptom_sessions_status",
        ),
        CheckConstraint(
            "triage_level IS NULL OR triage_level IN "
            "('non_urgent', 'semi_urgent', 'urgent', 'emergency')",
            name="ck_symptom_sessions_triage_level",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    symptoms: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    ai_analysis: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    triage_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalated_to: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=True
    )
    conversation_log: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    patient = relationship("User", foreign_keys=[patient_id], backref="symptom_sessions")
    escalated_to_user = relationship("User", foreign_keys=[escalated_to])

    def __repr__(self) -> str:
        return f"<SymptomSession {self.id} status={self.status} triage={self.triage_level}>"
