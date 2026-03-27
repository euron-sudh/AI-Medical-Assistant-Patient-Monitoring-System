"""Celery tasks for sending notifications across multiple channels."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from celery import shared_task

logger = logging.getLogger(__name__)

__all__ = ["send_notification", "send_email_notification", "send_sms_notification", "send_bulk_notifications"]


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification(self, notification_id: str) -> dict:
    """Dispatch a single notification via its configured channel."""
    from app.extensions import db
    from app.models.notification import Notification

    try:
        notif = db.session.get(Notification, uuid.UUID(notification_id))
        if notif is None:
            return {"status": "error", "message": "Notification not found"}
        if notif.channel == "email":
            logger.info("EMAIL -> user=%s", notif.user_id)
        elif notif.channel == "sms":
            logger.info("SMS -> user=%s", notif.user_id)
        elif notif.channel == "push":
            logger.info("PUSH -> user=%s", notif.user_id)
        notif.sent_at = datetime.now(timezone.utc)
        db.session.commit()
        return {"status": "sent", "notification_id": notification_id, "channel": notif.channel}
    except Exception as exc:
        logger.exception("Error sending notification %s", notification_id)
        db.session.rollback()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_notification(self, user_id: str, subject: str, body: str) -> dict:
    """Send a one-off email notification."""
    from app.extensions import db
    from app.models.user import User

    try:
        user = db.session.get(User, uuid.UUID(user_id))
        if user is None:
            return {"status": "error", "message": "User not found"}
        logger.info("Email -> %s subject=%s", user.email, subject)
        return {"status": "sent", "user_id": user_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_sms_notification(self, user_id: str, message: str) -> dict:
    """Send a one-off SMS notification."""
    from app.extensions import db
    from app.models.user import User

    try:
        user = db.session.get(User, uuid.UUID(user_id))
        if user is None:
            return {"status": "error", "message": "User not found"}
        phone = getattr(user, "phone", None)
        if not phone:
            return {"status": "skipped", "reason": "No phone number"}
        logger.info("SMS -> %s", phone)
        return {"status": "sent", "user_id": user_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task
def send_bulk_notifications(notification_ids: list[str]) -> dict:
    """Dispatch multiple notifications."""
    results = {"sent": 0, "failed": 0}
    for nid in notification_ids:
        try:
            send_notification.delay(nid)
            results["sent"] += 1
        except Exception:
            results["failed"] += 1
    return results
