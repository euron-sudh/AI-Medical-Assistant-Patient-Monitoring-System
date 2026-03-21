"""Care plan models — plans, goals, and activities."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text
from app.models.base import PortableJSON, PortableUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class CarePlan(db.Model):
    """Patient care plan created by a doctor, optionally AI-generated."""

    __tablename__ = "care_plans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'cancelled')",
            name="ck_care_plans_status",
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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    ai_recommendations: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
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
    doctor = relationship("User", foreign_keys=[doctor_id])
    goals = relationship("CarePlanGoal", back_populates="care_plan", cascade="all, delete-orphan")
    activities = relationship("CarePlanActivity", back_populates="care_plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CarePlan {self.title} ({self.status})>"


class CarePlanGoal(db.Model):
    """Measurable goal within a care plan."""

    __tablename__ = "care_plan_goals"
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'achieved', 'missed')",
            name="ck_care_plan_goals_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    care_plan_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    care_plan = relationship("CarePlan", back_populates="goals")

    def __repr__(self) -> str:
        return f"<CarePlanGoal {self.title} ({self.status})>"


class CarePlanActivity(db.Model):
    """Specific activity or task within a care plan."""

    __tablename__ = "care_plan_activities"
    __table_args__ = (
        CheckConstraint(
            "activity_type IN ('medication', 'exercise', 'diet', 'monitoring', 'appointment', 'other')",
            name="ck_care_plan_activities_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped')",
            name="ck_care_plan_activities_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PortableUUID(), primary_key=True, default=uuid.uuid4)
    care_plan_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), ForeignKey("care_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        PortableUUID(), ForeignKey("care_plan_goals.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    care_plan = relationship("CarePlan", back_populates="activities")
    goal = relationship("CarePlanGoal")

    def __repr__(self) -> str:
        return f"<CarePlanActivity {self.title} ({self.activity_type})>"
