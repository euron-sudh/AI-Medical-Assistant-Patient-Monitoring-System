"""Notification service — create, query, and manage user notifications."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.extensions import db
from app.models.notification import Notification
from app.schemas.notification_schema import CreateNotificationRequest, NotificationResponse


class NotificationService:
    """Handles creation, querying, and status management of notifications."""

    def create_notification(self, data: CreateNotificationRequest) -> NotificationResponse:
        """Create a new notification for a user.

        Args:
            data: Validated notification data.

        Returns:
            NotificationResponse with the created notification.
        """
        notification = Notification(
            user_id=uuid.UUID(data.user_id),
            type=data.type,
            title=data.title,
            message=data.message,
            data=data.data,
            channel=data.channel,
            sent_at=datetime.now(timezone.utc) if data.channel == "in_app" else None,
        )

        db.session.add(notification)
        db.session.commit()

        return self._to_response(notification)

    def get_user_notifications(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[NotificationResponse]:
        """Get notifications for a user.

        Args:
            user_id: UUID of the user.
            unread_only: If True, only return unread notifications.
            limit: Maximum number of notifications to return.
            offset: Number of notifications to skip.

        Returns:
            List of NotificationResponse ordered by created_at descending.
        """
        stmt = select(Notification).where(Notification.user_id == user_id)

        if unread_only:
            stmt = stmt.where(Notification.read == False)  # noqa: E712

        stmt = (
            stmt.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        notifications = db.session.execute(stmt).scalars().all()
        return [self._to_response(n) for n in notifications]

    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> NotificationResponse | None:
        """Mark a single notification as read.

        Args:
            notification_id: UUID of the notification.
            user_id: UUID of the notification owner (for authorization).

        Returns:
            Updated NotificationResponse, or None if not found or unauthorized.
        """
        stmt = (
            select(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        notification = db.session.execute(stmt).scalar_one_or_none()

        if notification is None:
            return None

        notification.read = True
        notification.read_at = datetime.now(timezone.utc)
        db.session.commit()

        return self._to_response(notification)

    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        """Mark all unread notifications as read for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Number of notifications updated.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            )
            .values(read=True, read_at=now, updated_at=now)
        )

        result = db.session.execute(stmt)
        db.session.commit()

        return result.rowcount

    def get_unread_count(self, user_id: uuid.UUID) -> int:
        """Get the count of unread notifications for a user.

        Args:
            user_id: UUID of the user.

        Returns:
            Number of unread notifications.
        """
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            )
        )
        notifications = db.session.execute(stmt).scalars().all()
        return len(notifications)

    def _to_response(self, notification: Notification) -> NotificationResponse:
        """Convert a Notification model to a NotificationResponse schema."""
        return NotificationResponse(
            id=str(notification.id),
            user_id=str(notification.user_id),
            type=notification.type,
            title=notification.title,
            message=notification.message,
            data=notification.data,
            read=notification.read,
            read_at=notification.read_at,
            channel=notification.channel,
            sent_at=notification.sent_at,
            created_at=notification.created_at,
        )


# Module-level instance for use by routes
notification_service = NotificationService()
