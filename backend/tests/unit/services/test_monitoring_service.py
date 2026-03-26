import uuid
from datetime import datetime, timezone

import pytest

from app.extensions import db
from app.models.alert import MonitoringAlert
from app.models.patient import PatientProfile
from app.models.user import User
from app.models.vitals import VitalsReading
from app.services.monitoring_service import monitoring_service


@pytest.fixture
def doctor_user(db):
    u = User(email="doc2@test.com", first_name="Doc", last_name="Two", role="doctor")
    u.set_password("securepass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def patient_user(db):
    u = User(email="pat2@test.com", first_name="Pat", last_name="Two", role="patient")
    u.set_password("securepass123")
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture
def assigned_patient_profile(db, doctor_user, patient_user):
    p = PatientProfile(
        user_id=patient_user.id,
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc).date(),
        assigned_doctor_id=doctor_user.id,
    )
    db.session.add(p)
    db.session.commit()
    return p


def test_list_monitored_patients_doctor_scoped(db, doctor_user, patient_user, assigned_patient_profile):
    r = VitalsReading(
        patient_id=patient_user.id,
        heart_rate=80,
        recorded_at=datetime.now(timezone.utc),
        created_by=doctor_user.id,
        is_manual_entry=True,
        is_anomalous=False,
    )
    db.session.add(r)
    db.session.commit()

    items = monitoring_service.list_monitored_patients(doctor_user.id, "doctor")
    assert len(items) == 1
    assert items[0]["patient_id"] == str(patient_user.id)
    assert items[0]["latest_vitals"]["heart_rate"] == 80


def test_resolve_critical_requires_notes(db, doctor_user, patient_user, assigned_patient_profile):
    alert = MonitoringAlert(
        patient_id=patient_user.id,
        vitals_reading_id=None,
        alert_type="spo2_low",
        severity="critical",
        title="SpO2 Critical",
        description="SpO2 is critically low",
        status="active",
        escalation_level=0,
    )
    db.session.add(alert)
    db.session.commit()

    with pytest.raises(ValueError):
        monitoring_service.resolve_alert(doctor_user.id, "doctor", alert.id, resolution_notes=None)

