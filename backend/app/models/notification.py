"""Notification model — multi-channel notifications for users."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import PortableUUID, PortableJSON


class Notification(db.Model):
    """User notification supporting in-app, email, SMS, and push channels."""

    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('in_app', 'email', 'sms', 'push')",
            name="ck_notifications_channel",
        ),
        Index("idx_notifications_user_id", "user_id"),
        Index(
            "idx_notifications_unread",
            "user_id",
            "read",
            postgresql_where="read = FALSE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PortableUUID(), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(PortableJSON(), nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_app"
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Notification {self.type}: {self.title} for user={self.user_id}>"
