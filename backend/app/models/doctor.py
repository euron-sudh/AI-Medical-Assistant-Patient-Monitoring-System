"""Doctor profile model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class DoctorProfile(db.Model):
    """Extended profile for users with role 'doctor'.

    Stores medical license, specialization, department, and availability.
    """

    __tablename__ = "doctor_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True
    )
    specialization: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False)
    license_state: Mapped[str | None] = mapped_column(String(5), nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consultation_fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    availability: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User", back_populates="doctor_profile", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<DoctorProfile {self.specialization} license={self.license_number}>"
