"""Conversation model — AI chat and voice conversation history."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableJSON, PortableUUID


class Conversation(db.Model):
    """AI conversation record for chat and voice interactions.

    Tracks messages exchanged between a patient and a specific AI agent,
    including conversation status and escalation details.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('symptom_analyst', 'report_reader', 'triage', 'voice', "
            "'drug_interaction', 'monitoring', 'follow_up', 'general')",
            name="ck_conversations_agent_type",
        ),
        CheckConstraint(
            "status IN ('active', 'closed', 'escalated')",
            name="ck_conversations_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    agent_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    messages: Mapped[list | None] = mapped_column(
        PortableJSON(), nullable=False, default=list
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    escalated_to: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=True
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", PortableJSON(), nullable=True
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
    patient = relationship("User", foreign_keys=[patient_id], backref="conversations")
    escalated_to_user = relationship("User", foreign_keys=[escalated_to])

    def __repr__(self) -> str:
        return f"<Conversation {self.id} agent={self.agent_type} status={self.status}>"
