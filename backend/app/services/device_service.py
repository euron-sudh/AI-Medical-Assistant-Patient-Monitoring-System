"""Device service — register/update devices and ingest device vitals."""

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.extensions import db
from app.models.device import Device
from app.models.patient import PatientProfile
from app.models.vitals import VitalsReading
from app.schemas.device_schema import DeviceVitalsIngestItem, RegisterDeviceRequest, UpdateDeviceRequest
from app.services.monitoring_service import monitoring_service


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class DeviceService:
    """Business logic for device registry and device->vitals ingestion."""

    _VITAL_TYPE_TO_FIELD: dict[str, tuple[str, str]] = {
        # vital_type -> (reading_field, value_kind)
        # value_kind in {"int", "decimal"}
        "heart_rate": ("heart_rate", "int"),
        "hr": ("heart_rate", "int"),
        "blood_pressure_systolic": ("blood_pressure_systolic", "int"),
        "bp_systolic": ("blood_pressure_systolic", "int"),
        "systolic_bp": ("blood_pressure_systolic", "int"),
        "blood_pressure_diastolic": ("blood_pressure_diastolic", "int"),
        "bp_diastolic": ("blood_pressure_diastolic", "int"),
        "diastolic_bp": ("blood_pressure_diastolic", "int"),
        "oxygen_saturation": ("oxygen_saturation", "decimal"),
        "spo2": ("oxygen_saturation", "decimal"),
        "spO2": ("oxygen_saturation", "decimal"),
        "temperature": ("temperature", "decimal"),
        "temp": ("temperature", "decimal"),
        "respiratory_rate": ("respiratory_rate", "int"),
        "rr": ("respiratory_rate", "int"),
        "blood_glucose": ("blood_glucose", "decimal"),
        "glucose": ("blood_glucose", "decimal"),
        "weight_kg": ("weight_kg", "decimal"),
        "weight": ("weight_kg", "decimal"),
        "pain_level": ("pain_level", "int"),
        "pain": ("pain_level", "int"),
    }

    def _is_assigned_patient(self, actor_id: uuid.UUID, actor_role: str, patient_id: uuid.UUID) -> bool:
        if actor_role == "admin":
            return True
        if actor_role not in {"doctor", "nurse"}:
            return False
        stmt = select(PatientProfile).where(
            PatientProfile.user_id == patient_id,
            PatientProfile.assigned_doctor_id == actor_id,
        )
        return db.session.execute(stmt).scalar_one_or_none() is not None

    def _check_device_access(self, actor_id: uuid.UUID, actor_role: str, device: Device) -> bool:
        if actor_role == "admin":
            return True
        if actor_role == "patient":
            return device.patient_id == actor_id
        return self._is_assigned_patient(actor_id, actor_role, device.patient_id)

    def list_patient_devices(self, viewer_id: uuid.UUID, viewer_role: str, patient_id: uuid.UUID) -> list[dict[str, Any]]:
        if viewer_role == "patient" and viewer_id != patient_id:
            return []
        if viewer_role in {"doctor", "nurse"} and not self._is_assigned_patient(viewer_id, viewer_role, patient_id):
            return []

        stmt = select(Device).where(Device.patient_id == patient_id).order_by(Device.updated_at.desc())
        devices = db.session.execute(stmt).scalars().all()
        return [self._device_to_dict(d) for d in devices]

    def register_device(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        patient_id: uuid.UUID,
        data: RegisterDeviceRequest,
    ) -> Device:
        if actor_role == "patient" and actor_id != patient_id:
            raise PermissionError("Cannot register devices for other patients")
        if actor_role in {"doctor", "nurse"} and not self._is_assigned_patient(actor_id, actor_role, patient_id):
            raise PermissionError("Not allowed to register device for this patient")

        device = Device(
            patient_id=patient_id,
            device_type=data.device_type,
            device_name=data.device_name,
            manufacturer=data.manufacturer,
            model=data.model,
            serial_number=data.serial_number,
            firmware_version=None,
            status="active",
            last_sync_at=None,
            battery_level=None,
            configuration=None,
        )
        db.session.add(device)
        db.session.commit()
        return device

    def update_device(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        device_id: uuid.UUID,
        data: UpdateDeviceRequest,
    ) -> Device | None:
        device = db.session.get(Device, device_id)
        if device is None:
            return None
        if not self._check_device_access(actor_id, actor_role, device):
            return None

        if data.firmware_version is not None:
            device.firmware_version = data.firmware_version
        if data.status is not None:
            # Ensure retired is allowed; rely on DB constraint for other invalid values
            device.status = data.status
        if data.configuration is not None:
            device.configuration = data.configuration

        try:
            db.session.add(device)
            db.session.commit()
            return device
        except Exception:
            db.session.rollback()
            return None

    def retire_device(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        device_id: uuid.UUID,
    ) -> Device | None:
        device = db.session.get(Device, device_id)
        if device is None:
            return None
        if not self._check_device_access(actor_id, actor_role, device):
            return None

        try:
            device.status = "retired"
            device.updated_at = _now_utc()
            db.session.commit()
            return device
        except Exception:
            db.session.rollback()
            return None

    def sync_device(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        device_id: uuid.UUID,
        battery_level: int | None,
    ) -> Device | None:
        """Record a sync event: update last_sync_at and optionally battery_level."""
        device = db.session.get(Device, device_id)
        if device is None:
            return None
        if not self._check_device_access(actor_id, actor_role, device):
            return None

        device.last_sync_at = _now_utc()
        if battery_level is not None:
            device.battery_level = battery_level
        db.session.commit()
        return device

    def ingest_device_data(
        self,
        actor_id: uuid.UUID,
        actor_role: str,
        device_id: uuid.UUID,
        items: list[DeviceVitalsIngestItem],
    ) -> list[VitalsReading] | None:
        device = db.session.get(Device, device_id)
        if device is None:
            return None
        if not self._check_device_access(actor_id, actor_role, device):
            return None
        if not items:
            return []

        # Group by timestamp -> one VitalsReading per timestamp.
        grouped: dict[datetime, dict[str, float]] = defaultdict(dict)
        for it in items:
            vital_key = it.vital_type.strip()
            vital_key_lc = vital_key.lower()
            mapping = self._VITAL_TYPE_TO_FIELD.get(vital_key) or self._VITAL_TYPE_TO_FIELD.get(vital_key_lc)
            if mapping is None:
                raise ValueError(f"Unsupported vital_type: {vital_key}")
            reading_field, kind = mapping
            if kind == "int":
                grouped[it.timestamp][reading_field] = int(it.value)
            else:
                grouped[it.timestamp][reading_field] = Decimal(str(it.value))

        created_readings: list[VitalsReading] = []
        for ts, fields in grouped.items():
            reading = VitalsReading(
                patient_id=device.patient_id,
                device_id=device.id,
                is_manual_entry=False,
                recorded_at=ts,
                created_by=actor_id,
                notes=None,
                is_anomalous=False,
                # Optional fields below
                heart_rate=fields.get("heart_rate"),
                blood_pressure_systolic=fields.get("blood_pressure_systolic"),
                blood_pressure_diastolic=fields.get("blood_pressure_diastolic"),
                temperature=fields.get("temperature"),
                oxygen_saturation=fields.get("oxygen_saturation"),
                respiratory_rate=fields.get("respiratory_rate"),
                blood_glucose=fields.get("blood_glucose"),
                weight_kg=fields.get("weight_kg"),
                pain_level=fields.get("pain_level"),
            )
            db.session.add(reading)
            db.session.commit()

            # Trigger monitoring evaluation for anomaly detection
            monitoring_service.analyze_and_handle_vitals_reading(reading, actor_id)
            created_readings.append(reading)

        device.last_sync_at = _now_utc()
        db.session.add(device)
        db.session.commit()

        return created_readings

    @staticmethod
    def _device_to_dict(d: Device) -> dict[str, Any]:
        return {
            "id": str(d.id),
            "patient_id": str(d.patient_id),
            "device_type": d.device_type,
            "device_name": d.device_name,
            "manufacturer": d.manufacturer,
            "model": d.model,
            "serial_number": d.serial_number,
            "firmware_version": d.firmware_version,
            "status": d.status,
            "last_sync_at": d.last_sync_at,
            "battery_level": d.battery_level,
            "configuration": d.configuration,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
        }


device_service = DeviceService()

