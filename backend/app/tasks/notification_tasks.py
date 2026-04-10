"""Celery tasks for sending notifications across multiple channels."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from celery import shared_task

logger = logging.getLogger(__name__)

__all__ = [
    "send_notification",
    "send_email_notification",
    "send_sms_notification",
    "send_bulk_notifications",
    "send_appointment_booked_email",
    "send_report_ready_email",
]


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
    """Send a one-off email notification to a user."""
    from app.extensions import db
    from app.integrations.email_client import email_client
    from app.models.user import User

    try:
        user = db.session.get(User, uuid.UUID(user_id))
        if user is None or not user.email:
            return {"status": "skipped", "reason": "user or email missing"}

        sent = email_client.send(to=user.email, subject=subject, html_body=body)
        return {"status": "sent" if sent else "noop", "user_id": user_id}
    except Exception as exc:
        logger.exception("send_email_notification failed user=%s", user_id)
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


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_appointment_booked_email(self, appointment_id: str) -> dict:
    """Send an appointment-booked confirmation email to the patient."""
    from flask import current_app

    from app.extensions import db
    from app.integrations.email_client import email_client
    from app.integrations.email_templates import appointment_booked_email
    from app.models.appointment import Appointment
    from app.models.doctor import DoctorProfile
    from app.models.user import User

    try:
        appt = db.session.get(Appointment, uuid.UUID(appointment_id))
        if appt is None:
            return {"status": "error", "message": "Appointment not found"}

        patient = db.session.get(User, appt.patient_id)
        doctor_user = db.session.get(User, appt.doctor_id)
        if patient is None or not patient.email:
            return {"status": "skipped", "reason": "patient or email missing"}

        doctor_name = "Your Doctor"
        specialty = ""
        if doctor_user:
            doctor_name = f"Dr. {doctor_user.first_name} {doctor_user.last_name}".strip()
            dprofile = (
                db.session.query(DoctorProfile)
                .filter_by(user_id=doctor_user.id)
                .first()
            )
            if dprofile:
                specialty = dprofile.specialization or ""

        base_url = current_app.config.get("APP_PUBLIC_URL", "")
        appt_url = f"{base_url}/patient/appointments" if base_url else "#"

        subject, html = appointment_booked_email(
            patient_name=patient.first_name or "there",
            doctor_name=doctor_name,
            specialty=specialty,
            scheduled_at=appt.scheduled_at,
            duration_minutes=appt.duration_minutes or 30,
            appointment_type=appt.appointment_type or "in_person",
            reason=appt.reason,
            appointment_url=appt_url,
        )

        ok = email_client.send(to=patient.email, subject=subject, html_body=html)
        logger.info(
            "appointment_booked_email result=%s appointment=%s to=%s",
            ok,
            appointment_id,
            patient.email,
        )
        return {"status": "sent" if ok else "noop", "appointment_id": appointment_id}
    except Exception as exc:
        logger.exception("send_appointment_booked_email failed id=%s", appointment_id)
        db.session.rollback()
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_report_ready_email(
    self,
    report_id: str,
    abnormal_findings: list[str] | None = None,
    recommended_specialist: str | None = None,
    urgency_label: str = "Routine",
) -> dict:
    """Send a 'report is ready' email with summary and appointment suggestion."""
    from flask import current_app

    from app.extensions import db
    from app.integrations.email_client import email_client
    from app.integrations.email_templates import report_ready_email
    from app.models.report import MedicalReport
    from app.models.user import User

    try:
        report = db.session.get(MedicalReport, uuid.UUID(report_id))
        if report is None:
            return {"status": "error", "message": "Report not found"}

        patient = db.session.get(User, report.patient_id)
        if patient is None or not patient.email:
            return {"status": "skipped", "reason": "patient or email missing"}

        base_url = current_app.config.get("APP_PUBLIC_URL", "")
        report_url = (
            f"{base_url}/patient/reports/{report.id}" if base_url else "#"
        )

        subject, html = report_ready_email(
            patient_name=patient.first_name or "there",
            report_title=report.title or "Medical Report",
            summary=(report.ai_summary or "Your report has been processed.")[:600],
            abnormal_findings=abnormal_findings or [],
            recommended_specialist=recommended_specialist,
            urgency_label=urgency_label,
            report_url=report_url,
        )

        ok = email_client.send(to=patient.email, subject=subject, html_body=html)
        logger.info(
            "report_ready_email result=%s report=%s to=%s",
            ok,
            report_id,
            patient.email,
        )
        return {"status": "sent" if ok else "noop", "report_id": report_id}
    except Exception as exc:
        logger.exception("send_report_ready_email failed id=%s", report_id)
        db.session.rollback()
        raise self.retry(exc=exc)
