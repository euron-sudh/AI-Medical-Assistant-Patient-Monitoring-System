"""Monitoring service — monitoring wall queries, alerts, thresholds, NEWS2 scoring."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, or_, select

from app.extensions import db
from app.models.alert import MonitoringAlert
from app.models.monitoring_threshold import MonitoringThreshold
from app.models.patient import PatientProfile
from app.models.user import User
from app.models.vitals import VitalsReading


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringService:
    """Business logic for monitoring endpoints."""

    def list_monitored_patients(self, viewer_user_id: uuid.UUID, viewer_role: str) -> list[dict[str, Any]]:
        """List patients with latest vitals snapshot and active alert count."""
        patient_users_stmt = (
            select(User, PatientProfile)
            .join(PatientProfile, PatientProfile.user_id == User.id)
            .where(User.role == "patient")
        )

        if viewer_role in {"doctor", "nurse"}:
            patient_users_stmt = patient_users_stmt.where(PatientProfile.assigned_doctor_id == viewer_user_id)
        elif viewer_role == "admin":
            pass
        else:
            return []

        rows = db.session.execute(patient_users_stmt).all()
        patient_ids = [row[0].id for row in rows]
        if not patient_ids:
            return []

        latest_readings = self._get_latest_vitals_by_patient(patient_ids)
        alert_counts = self._get_active_alert_counts(patient_ids)

        results: list[dict[str, Any]] = []
        for user, profile in rows:
            latest = latest_readings.get(user.id)
            results.append({
                "patient_id": str(user.id),
                "full_name": user.full_name,
                "assigned_doctor_id": str(profile.assigned_doctor_id) if profile.assigned_doctor_id else None,
                "latest_vitals": latest,
                "active_alert_count": int(alert_counts.get(user.id, 0)),
            })
        return results

    def get_patient_status(self, viewer_user_id: uuid.UUID, viewer_role: str, patient_id: uuid.UUID) -> dict[str, Any] | None:
        """Detailed monitoring status: latest vitals, NEWS2 score, active alerts, thresholds."""
        patient_info = self._get_patient_info(viewer_user_id, viewer_role, patient_id)
        if patient_info is None:
            return None

        latest = self._get_latest_vitals_by_patient([patient_id]).get(patient_id)
        thresholds = self.get_thresholds(patient_id)
        alerts = self.list_alerts(
            viewer_user_id=viewer_user_id,
            viewer_role=viewer_role,
            severity=None,
            patient_id=patient_id,
            status="active",
            start_date=None,
            end_date=None,
            limit=100,
            offset=0,
        )

        news2 = self.calculate_news2(latest) if latest else None
        return {
            "patient_id": str(patient_id),
            "full_name": patient_info["full_name"],
            "assigned_doctor_id": patient_info["assigned_doctor_id"],
            "latest_vitals": latest,
            "news2_score": news2,
            "thresholds": thresholds,
            "active_alerts": alerts,
        }

    def list_alerts(
        self,
        viewer_user_id: uuid.UUID,
        viewer_role: str,
        severity: str | None,
        patient_id: uuid.UUID | None,
        status: str | None,
        start_date: datetime | None,
        end_date: datetime | None,
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        """List alerts with filters and RBAC."""
        stmt = select(MonitoringAlert).order_by(MonitoringAlert.created_at.desc())

        if severity:
            stmt = stmt.where(MonitoringAlert.severity == severity)
        if patient_id:
            stmt = stmt.where(MonitoringAlert.patient_id == patient_id)
        if status:
            stmt = stmt.where(MonitoringAlert.status == status)
        if start_date:
            stmt = stmt.where(MonitoringAlert.created_at >= start_date)
        if end_date:
            stmt = stmt.where(MonitoringAlert.created_at <= end_date)

        # RBAC: doctors/nurses only see alerts for their assigned patients
        if viewer_role in {"doctor", "nurse"}:
            assigned_patient_ids_stmt = select(PatientProfile.user_id).where(
                PatientProfile.assigned_doctor_id == viewer_user_id
            )
            stmt = stmt.where(MonitoringAlert.patient_id.in_(assigned_patient_ids_stmt))
        elif viewer_role == "admin":
            pass
        else:
            return []

        stmt = stmt.offset(offset).limit(limit)
        alerts = db.session.execute(stmt).scalars().all()
        return [self._alert_to_dict(a) for a in alerts]

    def acknowledge_alert(self, actor_id: uuid.UUID, actor_role: str, alert_id: uuid.UUID) -> MonitoringAlert | None:
        if actor_role not in {"doctor", "nurse", "admin"}:
            return None

        alert = db.session.get(MonitoringAlert, alert_id)
        if alert is None:
            return None

        if actor_role in {"doctor", "nurse"}:
            if not self._is_assigned_patient(actor_id, alert.patient_id):
                return None

        alert.status = "acknowledged"
        alert.acknowledged_by = actor_id
        alert.acknowledged_at = _now_utc()
        db.session.commit()
        return alert

    def resolve_alert(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        alert_id: uuid.UUID,
        resolution_notes: str | None,
    ) -> MonitoringAlert | None:
        if actor_role not in {"doctor", "nurse", "admin"}:
            return None

        alert = db.session.get(MonitoringAlert, alert_id)
        if alert is None:
            return None

        if actor_role in {"doctor", "nurse"}:
            if not self._is_assigned_patient(actor_id, alert.patient_id):
                return None

        # Require notes for critical/emergency (mapped to severity == critical)
        if alert.severity == "critical" and not (resolution_notes and resolution_notes.strip()):
            raise ValueError("resolution_notes is required for critical alerts")

        alert.status = "resolved"
        alert.resolved_by = actor_id
        alert.resolved_at = _now_utc()
        alert.resolution_notes = resolution_notes.strip() if resolution_notes else None
        db.session.commit()
        return alert

    def escalate_alert(self, actor_id: uuid.UUID, actor_role: str, alert_id: uuid.UUID) -> MonitoringAlert | None:
        if actor_role not in {"doctor", "nurse", "admin"}:
            return None

        alert = db.session.get(MonitoringAlert, alert_id)
        if alert is None:
            return None

        if actor_role in {"doctor", "nurse"}:
            if not self._is_assigned_patient(actor_id, alert.patient_id):
                return None

        alert.escalation_level = int(alert.escalation_level or 0) + 1
        alert.escalated_at = _now_utc()
        db.session.commit()
        return alert

    def set_thresholds(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        patient_id: uuid.UUID,
        thresholds: dict[str, Any],
    ) -> MonitoringThreshold | None:
        if actor_role not in {"doctor", "nurse", "admin"}:
            return None

        if actor_role in {"doctor", "nurse"}:
            if not self._is_assigned_patient(actor_id, patient_id):
                return None

        existing = db.session.execute(
            select(MonitoringThreshold).where(MonitoringThreshold.patient_id == patient_id)
        ).scalar_one_or_none()

        if existing:
            existing.thresholds = thresholds or {}
            existing.updated_by = actor_id
            existing.updated_at = _now_utc()
            db.session.commit()
            return existing

        row = MonitoringThreshold(
            patient_id=patient_id,
            thresholds=thresholds or {},
            updated_by=actor_id,
        )
        db.session.add(row)
        db.session.commit()
        return row

    def get_thresholds(self, patient_id: uuid.UUID) -> dict[str, Any] | None:
        row = db.session.execute(
            select(MonitoringThreshold).where(MonitoringThreshold.patient_id == patient_id)
        ).scalar_one_or_none()
        if row is None:
            return None
        return {
            "patient_id": str(row.patient_id),
            "thresholds": row.thresholds or {},
            "updated_by": str(row.updated_by),
            "updated_at": row.updated_at,
        }

    # ----------------------------
    # Helpers
    # ----------------------------

    def _get_patient_info(self, viewer_user_id: uuid.UUID, viewer_role: str, patient_id: uuid.UUID) -> dict[str, Any] | None:
        stmt = (
            select(User, PatientProfile)
            .join(PatientProfile, PatientProfile.user_id == User.id)
            .where(User.id == patient_id)
            .where(User.role == "patient")
        )
        row = db.session.execute(stmt).one_or_none()
        if row is None:
            return None

        user, profile = row
        if viewer_role in {"doctor", "nurse"} and profile.assigned_doctor_id != viewer_user_id:
            return None
        if viewer_role not in {"doctor", "nurse", "admin"}:
            return None

        return {
            "full_name": user.full_name,
            "assigned_doctor_id": str(profile.assigned_doctor_id) if profile.assigned_doctor_id else None,
        }

    def _is_assigned_patient(self, doctor_user_id: uuid.UUID, patient_user_id: uuid.UUID) -> bool:
        stmt = select(PatientProfile).where(
            and_(
                PatientProfile.user_id == patient_user_id,
                PatientProfile.assigned_doctor_id == doctor_user_id,
            )
        )
        return db.session.execute(stmt).scalar_one_or_none() is not None

    def _get_latest_vitals_by_patient(self, patient_ids: list[uuid.UUID]) -> dict[uuid.UUID, dict[str, Any]]:
        # Subquery selecting latest recorded_at per patient
        latest_subq = (
            select(
                VitalsReading.patient_id.label("patient_id"),
                func.max(VitalsReading.recorded_at).label("max_recorded_at"),
            )
            .where(VitalsReading.patient_id.in_(patient_ids))
            .group_by(VitalsReading.patient_id)
            .subquery()
        )

        stmt = (
            select(VitalsReading)
            .join(
                latest_subq,
                and_(
                    VitalsReading.patient_id == latest_subq.c.patient_id,
                    VitalsReading.recorded_at == latest_subq.c.max_recorded_at,
                ),
            )
        )
        readings = db.session.execute(stmt).scalars().all()

        out: dict[uuid.UUID, dict[str, Any]] = {}
        for r in readings:
            out[r.patient_id] = {
                "recorded_at": r.recorded_at,
                "heart_rate": r.heart_rate,
                "blood_pressure_systolic": r.blood_pressure_systolic,
                "blood_pressure_diastolic": r.blood_pressure_diastolic,
                "temperature": float(r.temperature) if r.temperature is not None else None,
                "oxygen_saturation": float(r.oxygen_saturation) if r.oxygen_saturation is not None else None,
                "respiratory_rate": r.respiratory_rate,
                "blood_glucose": float(r.blood_glucose) if r.blood_glucose is not None else None,
                "weight_kg": float(r.weight_kg) if r.weight_kg is not None else None,
                "pain_level": r.pain_level,
                "device_id": str(r.device_id) if r.device_id else None,
                "is_anomalous": r.is_anomalous,
            }
        return out

    def _get_active_alert_counts(self, patient_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
        stmt = (
            select(MonitoringAlert.patient_id, func.count(MonitoringAlert.id))
            .where(MonitoringAlert.patient_id.in_(patient_ids))
            .where(MonitoringAlert.status == "active")
            .group_by(MonitoringAlert.patient_id)
        )
        rows = db.session.execute(stmt).all()
        return {pid: int(cnt) for pid, cnt in rows}

    @staticmethod
    def _alert_to_dict(a: MonitoringAlert) -> dict[str, Any]:
        return {
            "id": str(a.id),
            "patient_id": str(a.patient_id),
            "vitals_reading_id": str(a.vitals_reading_id) if a.vitals_reading_id else None,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "title": a.title,
            "description": a.description,
            "status": a.status,
            "acknowledged_by": str(a.acknowledged_by) if a.acknowledged_by else None,
            "acknowledged_at": a.acknowledged_at,
            "resolved_by": str(a.resolved_by) if a.resolved_by else None,
            "resolved_at": a.resolved_at,
            "resolution_notes": a.resolution_notes,
            "escalation_level": a.escalation_level,
            "escalated_at": a.escalated_at,
            "created_at": a.created_at,
            "updated_at": a.updated_at,
        }

    # ----------------------------
    # NEWS2 (simplified)
    # ----------------------------

    def calculate_news2(self, vitals: dict[str, Any]) -> int:
        """Compute a simplified NEWS2 score from a vitals snapshot.

        This implementation uses RR, SpO2, Temperature, Systolic BP, HR.
        Consciousness and supplemental O2 are not available in current schema.
        """
        score = 0

        rr = vitals.get("respiratory_rate")
        if rr is not None:
            if rr <= 8:
                score += 3
            elif 9 <= rr <= 11:
                score += 1
            elif 12 <= rr <= 20:
                score += 0
            elif 21 <= rr <= 24:
                score += 2
            else:  # >= 25
                score += 3

        spo2 = vitals.get("oxygen_saturation")
        if spo2 is not None:
            if spo2 <= 91:
                score += 3
            elif 92 <= spo2 <= 93:
                score += 2
            elif 94 <= spo2 <= 95:
                score += 1
            else:
                score += 0

        temp = vitals.get("temperature")
        if temp is not None:
            if temp <= 35.0:
                score += 3
            elif 35.1 <= temp <= 36.0:
                score += 1
            elif 36.1 <= temp <= 38.0:
                score += 0
            elif 38.1 <= temp <= 39.0:
                score += 1
            else:  # >= 39.1
                score += 2

        sbp = vitals.get("blood_pressure_systolic")
        if sbp is not None:
            if sbp <= 90:
                score += 3
            elif 91 <= sbp <= 100:
                score += 2
            elif 101 <= sbp <= 110:
                score += 1
            elif 111 <= sbp <= 219:
                score += 0
            else:  # >= 220
                score += 3

        hr = vitals.get("heart_rate")
        if hr is not None:
            if hr <= 40:
                score += 3
            elif 41 <= hr <= 50:
                score += 1
            elif 51 <= hr <= 90:
                score += 0
            elif 91 <= hr <= 110:
                score += 1
            elif 111 <= hr <= 130:
                score += 2
            else:  # >= 131
                score += 3

        return int(score)

    # ----------------------------
    # Monitoring evaluation
    # ----------------------------

    def analyze_and_handle_vitals_reading(self, reading: VitalsReading, actor_id: uuid.UUID) -> None:
        """Evaluate a newly ingested vitals reading for anomalies and create alerts.

        This acts as the "monitoring agent" entrypoint for now (sync path).
        Future: enqueue this via Celery for >500ms processing and notifications.
        """
        patient_id = reading.patient_id

        # Fetch thresholds (custom overrides; fall back to defaults)
        thresholds = self._merge_thresholds(patient_id)

        anomalies: list[dict[str, Any]] = []
        overall_severity: str | None = None

        for vital_key, vital_cfg in thresholds.items():
            value = self._get_vital_value_from_reading(reading, vital_key)
            if value is None:
                continue

            breach = self._check_breach(vital_key, value, vital_cfg)
            if breach is None:
                continue

            anomalies.append({
                "vital": vital_key,
                "value": value,
                "severity": breach["severity"],
                "expected": breach["expected"],
            })

            if breach["severity"] == "critical":
                overall_severity = "critical"
            elif overall_severity is None:
                overall_severity = "high"

        if not anomalies or overall_severity is None:
            reading.is_anomalous = False
            db.session.add(reading)
            db.session.commit()
            return

        reading.is_anomalous = True
        db.session.add(reading)
        db.session.commit()

        # Single alert per reading (keeps active alert counts stable/predictable)
        alert = MonitoringAlert(
            patient_id=patient_id,
            vitals_reading_id=reading.id,
            alert_type="vitals_threshold_breach",
            severity=overall_severity,
            title="Vitals threshold breach detected",
            description=f"Anomalous vitals detected for patient {patient_id}.",
            ai_analysis={
                "anomalies": anomalies,
                "news2_score": self.calculate_news2(self._reading_to_snapshot(reading)),
                "generated_at": _now_utc().isoformat(),
            },
            status="active",
            escalated_at=None,
            escalation_level=0,
        )
        db.session.add(alert)
        db.session.commit()

    def _reading_to_snapshot(self, reading: VitalsReading) -> dict[str, Any]:
        return {
            "recorded_at": reading.recorded_at,
            "heart_rate": reading.heart_rate,
            "blood_pressure_systolic": reading.blood_pressure_systolic,
            "blood_pressure_diastolic": reading.blood_pressure_diastolic,
            "temperature": float(reading.temperature) if reading.temperature is not None else None,
            "oxygen_saturation": float(reading.oxygen_saturation) if reading.oxygen_saturation is not None else None,
            "respiratory_rate": reading.respiratory_rate,
            "blood_glucose": float(reading.blood_glucose) if reading.blood_glucose is not None else None,
            "weight_kg": float(reading.weight_kg) if reading.weight_kg is not None else None,
            "pain_level": reading.pain_level,
            "device_id": str(reading.device_id) if reading.device_id else None,
            "is_anomalous": reading.is_anomalous,
        }

    def _merge_thresholds(self, patient_id: uuid.UUID) -> dict[str, dict[str, Any]]:
        defaults: dict[str, dict[str, Any]] = {
            "heart_rate": {"min": 50, "max": 110, "critical_min": 40, "critical_max": 130},
            "blood_pressure_systolic": {"min": 90, "max": 140, "critical_min": 80, "critical_max": 180},
            "blood_pressure_diastolic": {"min": 60, "max": 90, "critical_min": 50, "critical_max": 120},
            "oxygen_saturation": {"min": 95, "max": 100, "critical_min": 90, "critical_max": 100},
            "temperature": {"min": 36.0, "max": 37.8, "critical_min": 35.0, "critical_max": 39.5},
            "respiratory_rate": {"min": 12, "max": 24, "critical_min": 8, "critical_max": 30},
            "blood_glucose": {"min": 70, "max": 180, "critical_min": 50, "critical_max": 300},
            "weight_kg": {},
            "pain_level": {"min": 0, "max": 3, "critical_max": 7},
        }

        row = self.get_thresholds(patient_id)
        if not row:
            return defaults

        custom = row.get("thresholds") or {}
        merged: dict[str, dict[str, Any]] = dict(defaults)
        for k, v in custom.items():
            if isinstance(v, dict):
                merged[k] = v
        return merged

    def _get_vital_value_from_reading(self, reading: VitalsReading, vital_key: str) -> Any | None:
        # vital_key is expected to match our threshold keys.
        if vital_key == "heart_rate":
            return reading.heart_rate
        if vital_key == "blood_pressure_systolic":
            return reading.blood_pressure_systolic
        if vital_key == "blood_pressure_diastolic":
            return reading.blood_pressure_diastolic
        if vital_key == "oxygen_saturation":
            return float(reading.oxygen_saturation) if reading.oxygen_saturation is not None else None
        if vital_key == "temperature":
            return float(reading.temperature) if reading.temperature is not None else None
        if vital_key == "respiratory_rate":
            return reading.respiratory_rate
        if vital_key == "blood_glucose":
            return float(reading.blood_glucose) if reading.blood_glucose is not None else None
        if vital_key == "weight_kg":
            return float(reading.weight_kg) if reading.weight_kg is not None else None
        if vital_key == "pain_level":
            return reading.pain_level
        return None

    def _check_breach(self, vital_key: str, value: Any, vital_cfg: dict[str, Any]) -> dict[str, Any] | None:
        """Return breach details or None."""
        if not vital_cfg:
            return None

        min_v = vital_cfg.get("min")
        max_v = vital_cfg.get("max")
        critical_min = vital_cfg.get("critical_min")
        critical_max = vital_cfg.get("critical_max")

        # Determine critical breach first if configured.
        if critical_min is not None and value < critical_min:
            return {"severity": "critical", "expected": {"min": critical_min, "max": critical_max}}
        if critical_max is not None and value > critical_max:
            return {"severity": "critical", "expected": {"min": critical_min, "max": critical_max}}

        # Then normal-range breach.
        if min_v is not None and value < min_v:
            return {"severity": "high", "expected": {"min": min_v, "max": max_v}}
        if max_v is not None and value > max_v:
            return {"severity": "high", "expected": {"min": min_v, "max": max_v}}

        return None


monitoring_service = MonitoringService()

