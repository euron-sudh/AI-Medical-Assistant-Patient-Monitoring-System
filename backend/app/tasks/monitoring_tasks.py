"""Celery tasks for vitals monitoring and threshold checks."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from celery import shared_task

logger = logging.getLogger(__name__)

__all__ = ["check_patient_vitals", "check_all_patient_vitals", "escalate_unacknowledged_alerts"]

DEFAULT_THRESHOLDS = {
    "heart_rate": {"min": 50, "max": 120},
    "blood_pressure_systolic": {"min": 80, "max": 180},
    "blood_pressure_diastolic": {"min": 50, "max": 110},
    "oxygen_saturation": {"min": 90},
    "temperature": {"min": 95.0, "max": 103.0},
    "respiratory_rate": {"min": 10, "max": 30},
    "blood_glucose": {"min": 60, "max": 300},
}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_patient_vitals(self, patient_id: str) -> dict:
    """Check latest vitals for a patient against thresholds."""
    from app.extensions import db
    from app.models.vitals import VitalsReading
    from app.models.monitoring_threshold import MonitoringThreshold
    from app.models.alert import MonitoringAlert

    try:
        pid = uuid.UUID(patient_id)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
        reading = (
            db.session.query(VitalsReading)
            .filter(VitalsReading.patient_id == pid, VitalsReading.recorded_at >= cutoff)
            .order_by(VitalsReading.recorded_at.desc())
            .first()
        )
        if reading is None:
            return {"status": "ok", "message": "No recent readings"}

        custom = db.session.query(MonitoringThreshold).filter_by(patient_id=pid).first()
        thresholds = custom.thresholds if custom else DEFAULT_THRESHOLDS
        alerts_created = []

        for vital_name, bounds in thresholds.items():
            value = getattr(reading, vital_name, None)
            if value is None:
                continue
            v = float(value) if isinstance(value, Decimal) else value
            min_val, max_val = bounds.get("min"), bounds.get("max")
            breach = None

            if min_val is not None and v < min_val:
                breach = "low"
            elif max_val is not None and v > max_val:
                breach = "high"

            if breach:
                label = vital_name.replace("_", " ").title()
                threshold_val = max_val if breach == "high" else min_val
                deviation = abs(v - threshold_val) / max(abs(threshold_val), 1)
                severity = "critical" if deviation > 0.3 else "high" if deviation > 0.15 else "medium"
                direction = "Elevated" if breach == "high" else "Low"
                alert = MonitoringAlert(
                    patient_id=pid,
                    vitals_reading_id=reading.id,
                    alert_type=vital_name,
                    severity=severity,
                    title=f"{direction} {label}",
                    description=f"{label} reading {v} vs threshold {threshold_val}",
                    status="active",
                )
                db.session.add(alert)
                alerts_created.append({"vital": vital_name, "value": v, "severity": severity})
                reading.is_anomalous = True

        if alerts_created:
            db.session.commit()
            try:
                from app.extensions import socketio
                from app.api.websocket.vitals_stream import broadcast_vitals_alert
                for a in alerts_created:
                    broadcast_vitals_alert(socketio, patient_id, a)
            except Exception:
                pass

        return {"status": "checked", "patient_id": patient_id, "alerts": len(alerts_created)}
    except Exception as exc:
        db.session.rollback()
        raise self.retry(exc=exc)


@shared_task
def check_all_patient_vitals() -> dict:
    """Periodic: check vitals for all patients with recent readings."""
    from app.extensions import db
    from app.models.vitals import VitalsReading

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    patient_ids = (
        db.session.query(VitalsReading.patient_id)
        .filter(VitalsReading.recorded_at >= cutoff)
        .distinct()
        .all()
    )
    count = 0
    for (pid,) in patient_ids:
        check_patient_vitals.delay(str(pid))
        count += 1
    return {"patients_checked": count}


@shared_task
def escalate_unacknowledged_alerts() -> dict:
    """Periodic: escalate alerts not acknowledged within 15 min."""
    from app.extensions import db
    from app.models.alert import MonitoringAlert

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    alerts = (
        db.session.query(MonitoringAlert)
        .filter(
            MonitoringAlert.status == "active",
            MonitoringAlert.created_at <= cutoff,
            MonitoringAlert.escalation_level < 3,
        )
        .all()
    )
    escalated = 0
    for alert in alerts:
        alert.escalation_level += 1
        alert.escalated_at = datetime.now(timezone.utc)
        escalated += 1
    if escalated:
        db.session.commit()
    return {"escalated": escalated}
