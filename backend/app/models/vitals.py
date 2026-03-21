"""VitalsReading model — patient vital sign measurements."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text
from app.models.base import PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class VitalsReading(db.Model):
    """Individual vital sign reading from manual entry or IoT device.

    Stores heart rate, blood pressure, SpO2, temperature, respiratory rate,
    blood glucose, weight, and pain level. High-frequency device data is
    also mirrored to InfluxDB for time-series queries.
    """

    __tablename__ = "vitals_readings"
    __table_args__ = (
        CheckConstraint("pain_level BETWEEN 0 AND 10", name="ck_vitals_pain_level"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id"), nullable=False, index=True
    )
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_pressure_diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    oxygen_saturation: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blood_glucose: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1), nullable=True)
    pain_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("devices.id"), nullable=True, index=True
    )
    is_manual_entry: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_anomalous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
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
    patient = relationship("User", foreign_keys=[patient_id], backref="vitals_readings")
    device = relationship("Device", back_populates="vitals_readings")

    def __repr__(self) -> str:
        return f"<VitalsReading {self.id} patient={self.patient_id} HR={self.heart_rate}>"
