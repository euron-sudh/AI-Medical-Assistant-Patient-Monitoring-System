import uuid
from datetime import datetime, timezone

import pytest

from sqlalchemy import select

from app.models.device import Device
from app.models.patient import PatientProfile
from app.models.user import User
from app.models.vitals import VitalsReading
from app.models.alert import MonitoringAlert
from app.schemas.device_schema import DeviceVitalsIngestItem, RegisterDeviceRequest
from app.services.device_service import device_service


@pytest.fixture
def doctor(db):
    u = User(email="devicedoc@test.com", first_name="Dev", last_name="Doc", role="doctor")
    u.set_password("securepass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def patient(db):
    u = User(email="devicepat@test.com", first_name="Dev", last_name="Pat", role="patient")
    u.set_password("securepass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def assigned_profile(db, doctor, patient):
    p = PatientProfile(
        user_id=patient.id,
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc).date(),
        assigned_doctor_id=doctor.id,
    )
    db.session.add(p)
    db.session.commit()
    return p


def test_ingest_device_data_creates_vitals_and_alerts(db, doctor, patient, assigned_profile):
    device = Device(
        patient_id=patient.id,
        device_type="wearable",
        device_name="Test Wearable",
        manufacturer="Acme",
        model="W-1",
        serial_number="SN-1",
        firmware_version="1.0",
        status="active",
    )
    db.session.add(device)
    db.session.commit()

    ts = datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    items = [
        DeviceVitalsIngestItem(vital_type="heart_rate", value=200, timestamp=ts),
    ]
    created = device_service.ingest_device_data(doctor.id, "doctor", device.id, items)
    assert created is not None
    assert len(created) == 1

    reading = db.session.get(VitalsReading, created[0].id)
    assert reading is not None
    assert reading.is_anomalous is True

    alerts = db.session.execute(
        select(MonitoringAlert).where(MonitoringAlert.patient_id == patient.id)
    ).scalars().all()
    assert len(alerts) == 1
    assert alerts[0].status == "active"
    assert alerts[0].severity in {"high", "critical"}

