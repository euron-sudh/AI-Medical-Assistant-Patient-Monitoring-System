"""MonitoringThreshold model — per-patient custom vitals thresholds.

Stores customizable min/max ranges per vital for alerting/anomaly detection.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import PortableJSON, PortableUUID


class MonitoringThreshold(db.Model):
    """Custom monitoring thresholds for a patient.

    `thresholds` is a JSON object such as:
      {
        "heart_rate": {"min": 45, "max": 110},
        "oxygen_saturation": {"min": 92},
        "temperature": {"max": 100.4}
      }
    """

    __tablename__ = "monitoring_thresholds"
    __table_args__ = (
        UniqueConstraint("patient_id", name="uq_monitoring_thresholds_patient_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    thresholds: Mapped[dict] = mapped_column(PortableJSON(), nullable=False, default=dict)
    updated_by: Mapped[uuid.UUID] = mapped_column(
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

    patient = relationship("User", foreign_keys=[patient_id])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<MonitoringThreshold patient={self.patient_id}>"

