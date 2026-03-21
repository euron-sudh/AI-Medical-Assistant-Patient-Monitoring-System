"""Seed script for Render deployment — creates full demo data linked to the 3 test users."""

import os
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()


def utcnow():
    return datetime.now(timezone.utc)


def seed():
    with app.app_context():
        # Get the 3 demo users
        patient_user = User.query.filter_by(email="patient@demo.dev").first()
        doctor_user = User.query.filter_by(email="doctor@demo.dev").first()
        admin_user = User.query.filter_by(email="admin@demo.dev").first()

        if not patient_user or not doctor_user:
            print("ERROR: Demo users not found. Run the app first to auto-create them.")
            return

        print(f"Found users: patient={patient_user.id}, doctor={doctor_user.id}, admin={admin_user.id}")

        # === PATIENT PROFILE ===
        from app.models.patient import PatientProfile, MedicalHistory, Allergy
        if PatientProfile.query.filter_by(user_id=patient_user.id).first():
            print("Patient profile already exists, skipping profiles...")
        else:
            profile = PatientProfile(
                user_id=patient_user.id,
                date_of_birth=date(1990, 5, 15),
                gender="male",
                blood_type="O+",
                height_cm=175.0,
                weight_kg=78.5,
                assigned_doctor_id=doctor_user.id,
            )
            db.session.add(profile)
            db.session.flush()
            print(f"Created patient profile: {profile.id}")

            # Medical history
            conditions = [
                ("Type 2 Diabetes", "E11", date(2022, 3, 15), "active", "Managed with metformin"),
                ("Hypertension", "I10", date(2021, 8, 10), "active", "Stage 1, on lisinopril"),
                ("Seasonal Allergies", "J30.1", date(2019, 4, 1), "chronic", "Spring/fall flare-ups"),
                ("Appendectomy", "K35", date(2015, 11, 20), "resolved", "Surgical removal, no complications"),
                ("COVID-19", "U07.1", date(2023, 1, 5), "resolved", "Mild case, fully recovered"),
            ]
            for name, icd, diag_date, status, notes in conditions:
                h = MedicalHistory(
                    patient_id=profile.id,
                    condition_name=name,
                    icd_10_code=icd,
                    diagnosis_date=diag_date,
                    status=status,
                    notes=notes,
                    diagnosed_by=doctor_user.id,
                    created_by=doctor_user.id,
                )
                db.session.add(h)
            print("Created 5 medical history entries")

            # Allergies
            allergies = [
                ("Penicillin", "Severe rash and hives", "severe"),
                ("Shellfish", "Throat swelling, difficulty breathing", "life_threatening"),
                ("Pollen", "Sneezing, runny nose, itchy eyes", "mild"),
            ]
            for allergen, reaction, severity in allergies:
                a = Allergy(
                    patient_id=profile.id,
                    allergen=allergen,
                    reaction=reaction,
                    severity=severity,
                    diagnosed_date=date(2020, 6, 1),
                    created_by=doctor_user.id,
                )
                db.session.add(a)
            print("Created 3 allergies")

        db.session.commit()
        profile = PatientProfile.query.filter_by(user_id=patient_user.id).first()

        # === DOCTOR PROFILE ===
        from app.models.doctor import DoctorProfile
        if not DoctorProfile.query.filter_by(user_id=doctor_user.id).first():
            doc_profile = DoctorProfile(
                user_id=doctor_user.id,
                specialization="Internal Medicine",
                license_number="MD-2024-78432",
                license_state="CA",
                years_of_experience=12,
                department="General Medicine",
                bio="Board-certified internist with 12 years experience in primary care and chronic disease management.",
            )
            db.session.add(doc_profile)
            db.session.commit()
            print("Created doctor profile")

        # === VITALS (30 readings over past 30 days) ===
        from app.models.vitals import VitalsReading
        if VitalsReading.query.filter_by(patient_id=patient_user.id).count() == 0:
            import random
            random.seed(42)
            for i in range(30):
                recorded = utcnow() - timedelta(days=29 - i, hours=random.randint(6, 20))
                is_anomalous = i in [5, 12, 22]  # Some abnormal readings
                v = VitalsReading(
                    patient_id=patient_user.id,
                    heart_rate=random.randint(58, 105) if not is_anomalous else random.choice([52, 115, 130]),
                    blood_pressure_systolic=random.randint(110, 145) if not is_anomalous else random.choice([160, 170]),
                    blood_pressure_diastolic=random.randint(65, 92) if not is_anomalous else random.choice([100, 105]),
                    temperature=round(random.uniform(36.2, 37.3), 1) if not is_anomalous else 38.8,
                    oxygen_saturation=round(random.uniform(95.5, 99.5), 1) if not is_anomalous else 91.0,
                    respiratory_rate=random.randint(12, 20) if not is_anomalous else 28,
                    blood_glucose=round(random.uniform(85, 140), 1),
                    is_manual_entry=random.choice([True, False]),
                    is_anomalous=is_anomalous,
                    recorded_at=recorded,
                    created_by=patient_user.id,
                )
                db.session.add(v)
            db.session.commit()
            print("Created 30 vitals readings")

        # === MEDICATIONS ===
        from app.models.medication import Medication
        if Medication.query.filter_by(patient_id=patient_user.id).count() == 0:
            meds = [
                ("Metformin", "500mg", "Twice daily", "oral", "active", "Type 2 Diabetes management", 3),
                ("Lisinopril", "10mg", "Once daily", "oral", "active", "Blood pressure control", 5),
                ("Atorvastatin", "20mg", "Once daily at bedtime", "oral", "active", "Cholesterol management", 2),
                ("Cetirizine", "10mg", "Once daily as needed", "oral", "active", "Seasonal allergy relief", 0),
                ("Amoxicillin", "500mg", "Three times daily", "oral", "completed", "Upper respiratory infection", 0),
                ("Ibuprofen", "400mg", "As needed for pain", "oral", "discontinued", "Replaced with acetaminophen", 0),
            ]
            for name, dosage, freq, route, status, reason, refills in meds:
                m = Medication(
                    patient_id=patient_user.id,
                    name=name,
                    dosage=dosage,
                    frequency=freq,
                    route=route,
                    status=status,
                    reason=reason,
                    refills_remaining=refills,
                    prescribed_by=doctor_user.id,
                    start_date=date(2024, 1, 15),
                    end_date=date(2025, 1, 15) if status != "active" else None,
                    created_by=doctor_user.id,
                )
                db.session.add(m)
            db.session.commit()
            print("Created 6 medications")

        # === MEDICAL REPORTS ===
        from app.models.report import MedicalReport, LabValue
        if MedicalReport.query.filter_by(patient_id=patient_user.id).count() == 0:
            reports_data = [
                ("lab", "Complete Blood Count (CBC)", "completed",
                 "All values within normal range. WBC slightly elevated suggesting mild infection.",
                 [("WBC", 11.2, "10^3/uL", 4.5, 11.0, True), ("RBC", 4.8, "10^6/uL", 4.5, 5.5, False),
                  ("Hemoglobin", 14.5, "g/dL", 13.5, 17.5, False), ("Platelets", 250, "10^3/uL", 150, 400, False)]),
                ("lab", "Comprehensive Metabolic Panel", "completed",
                 "Blood glucose slightly elevated at 128 mg/dL. Kidney and liver function normal.",
                 [("Glucose", 128, "mg/dL", 70, 100, True), ("BUN", 18, "mg/dL", 7, 20, False),
                  ("Creatinine", 1.0, "mg/dL", 0.7, 1.3, False), ("ALT", 25, "U/L", 7, 56, False)]),
                ("lab", "Lipid Panel", "completed",
                 "Total cholesterol borderline high. LDL elevated — continue statin therapy.",
                 [("Total Cholesterol", 215, "mg/dL", 0, 200, True), ("LDL", 138, "mg/dL", 0, 100, True),
                  ("HDL", 52, "mg/dL", 40, 60, False), ("Triglycerides", 165, "mg/dL", 0, 150, True)]),
                ("lab", "HbA1c Test", "completed",
                 "HbA1c at 7.2% indicates fair diabetic control. Target < 7.0%.",
                 [("HbA1c", 7.2, "%", 0, 5.7, True)]),
                ("imaging", "Chest X-Ray", "reviewed",
                 "Clear lung fields bilaterally. Heart size normal. No acute abnormalities.", []),
                ("other", "ECG/EKG Report", "reviewed",
                 "Normal sinus rhythm. No ST changes. No arrhythmias detected.", []),
            ]
            for rtype, title, status, summary, labs in reports_data:
                r = MedicalReport(
                    patient_id=patient_user.id,
                    report_type=rtype,
                    title=title,
                    status=status,
                    ai_summary=summary,
                    created_by=doctor_user.id,
                    reviewed_by=doctor_user.id if status == "reviewed" else None,
                    reviewed_at=utcnow() if status == "reviewed" else None,
                )
                db.session.add(r)
                db.session.flush()
                for test_name, value, unit, ref_min, ref_max, abnormal in labs:
                    lv = LabValue(
                        report_id=r.id,
                        patient_id=patient_user.id,
                        test_name=test_name,
                        value=value,
                        unit=unit,
                        reference_min=ref_min,
                        reference_max=ref_max,
                        is_abnormal=abnormal,
                        collected_at=utcnow() - timedelta(days=7),
                    )
                    db.session.add(lv)
            db.session.commit()
            print("Created 6 reports with 13 lab values")

        # === APPOINTMENTS ===
        from app.models.appointment import Appointment
        if Appointment.query.filter_by(patient_id=patient_user.id).count() == 0:
            appts = [
                ("in_person", "completed", -14, "Follow-up: diabetes management review"),
                ("telemedicine", "completed", -7, "Blood pressure check and medication review"),
                ("in_person", "completed", -3, "Lab results discussion — lipid panel and HbA1c"),
                ("telemedicine", "scheduled", 2, "Monthly check-in — vitals review"),
                ("in_person", "scheduled", 8, "Quarterly diabetes management visit"),
                ("follow_up", "scheduled", 15, "Follow-up: medication adjustment if needed"),
                ("in_person", "cancelled", -21, "Annual physical — rescheduled"),
            ]
            for atype, status, days_offset, reason in appts:
                scheduled = utcnow() + timedelta(days=days_offset)
                a = Appointment(
                    patient_id=patient_user.id,
                    doctor_id=doctor_user.id,
                    appointment_type=atype,
                    status=status,
                    scheduled_at=scheduled.replace(hour=10, minute=0),
                    duration_minutes=30,
                    reason=reason,
                    created_by=patient_user.id,
                )
                db.session.add(a)
            db.session.commit()
            print("Created 7 appointments")

        # === CARE PLANS ===
        from app.models.care_plan import CarePlan, CarePlanGoal, CarePlanActivity
        if CarePlan.query.filter_by(patient_id=patient_user.id).count() == 0:
            cp = CarePlan(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                title="Diabetes Management Plan",
                description="Comprehensive plan to manage Type 2 Diabetes through medication, diet, exercise, and regular monitoring.",
                status="active",
                start_date=date(2024, 6, 1),
                created_by=doctor_user.id,
            )
            db.session.add(cp)
            db.session.flush()

            goals = [
                ("Reduce HbA1c to < 7.0%", "Current: 7.2%", "7.0", "7.2", "%", "in_progress"),
                ("Maintain blood pressure < 130/80", "Monitor daily", "130", "140", "mmHg", "in_progress"),
                ("Lose 5kg in 6 months", "Current weight: 78.5kg", "73.5", "78.5", "kg", "in_progress"),
                ("Exercise 150 min/week", "Walking and swimming", "150", "90", "min/week", "in_progress"),
            ]
            for title, desc, target, current, unit, status in goals:
                g = CarePlanGoal(
                    care_plan_id=cp.id,
                    title=title,
                    description=desc,
                    target_value=target,
                    current_value=current,
                    unit=unit,
                    status=status,
                    target_date=date(2025, 12, 31),
                )
                db.session.add(g)
                db.session.flush()

            activities = [
                (cp.id, "Take Metformin 500mg twice daily", "medication", "in_progress"),
                (cp.id, "Check blood glucose before meals", "monitoring", "in_progress"),
                (cp.id, "Walk 30 minutes, 5 days/week", "exercise", "in_progress"),
                (cp.id, "Follow low-carb meal plan", "diet", "in_progress"),
                (cp.id, "Monthly lab work — HbA1c and metabolic panel", "monitoring", "pending"),
                (cp.id, "Quarterly doctor visit", "appointment", "pending"),
            ]
            for plan_id, title, atype, status in activities:
                act = CarePlanActivity(
                    care_plan_id=plan_id,
                    title=title,
                    activity_type=atype,
                    status=status,
                    frequency="Daily" if atype in ("medication", "monitoring", "diet") else "Weekly" if atype == "exercise" else "Quarterly",
                )
                db.session.add(act)

            # Second care plan
            cp2 = CarePlan(
                patient_id=patient_user.id,
                doctor_id=doctor_user.id,
                title="Hypertension Control Plan",
                description="Plan to manage blood pressure through medication and lifestyle changes.",
                status="active",
                start_date=date(2024, 8, 1),
                created_by=doctor_user.id,
            )
            db.session.add(cp2)
            db.session.flush()

            g2 = CarePlanGoal(
                care_plan_id=cp2.id,
                title="Reduce sodium intake to < 2300mg/day",
                target_value="2300",
                current_value="3100",
                unit="mg/day",
                status="in_progress",
            )
            db.session.add(g2)

            db.session.commit()
            print("Created 2 care plans with 4 goals and 6 activities")

        # === MONITORING ALERTS ===
        from app.models.alert import MonitoringAlert
        if MonitoringAlert.query.filter_by(patient_id=patient_user.id).count() == 0:
            alerts = [
                ("heart_rate", "high", "Elevated heart rate: 130 bpm", "Heart rate exceeded threshold of 100 bpm. Patient vitals show sustained tachycardia.", "active"),
                ("blood_pressure", "critical", "High blood pressure: 170/105 mmHg", "Systolic BP exceeds critical threshold of 160 mmHg. Immediate physician review recommended.", "active"),
                ("oxygen_saturation", "critical", "Low SpO2: 91%", "Oxygen saturation dropped below 92%. Monitor closely for respiratory distress.", "acknowledged"),
                ("temperature", "medium", "Mild fever: 38.8C", "Temperature slightly elevated. Monitor for infection signs.", "resolved"),
                ("blood_glucose", "low", "Elevated glucose: 185 mg/dL", "Post-meal glucose spike above 180 mg/dL threshold.", "resolved"),
            ]
            for vital_type, severity, title, desc, status in alerts:
                alert = MonitoringAlert(
                    patient_id=patient_user.id,
                    alert_type=vital_type,
                    severity=severity,
                    title=title,
                    description=desc,
                    status=status,
                    acknowledged_by=doctor_user.id if status in ("acknowledged", "resolved") else None,
                    acknowledged_at=utcnow() - timedelta(hours=2) if status in ("acknowledged", "resolved") else None,
                    resolved_by=doctor_user.id if status == "resolved" else None,
                    resolved_at=utcnow() - timedelta(hours=1) if status == "resolved" else None,
                )
                db.session.add(alert)
            db.session.commit()
            print("Created 5 monitoring alerts")

        # === NOTIFICATIONS ===
        from app.models.notification import Notification
        if Notification.query.filter_by(user_id=patient_user.id).count() == 0:
            notifs = [
                (patient_user.id, "appointment_reminder", "Upcoming Appointment", "You have an appointment with Dr. Demo Doctor in 2 days."),
                (patient_user.id, "medication_reminder", "Medication Due", "Time to take Metformin 500mg."),
                (patient_user.id, "report_ready", "Lab Results Available", "Your Lipid Panel results are ready for review."),
                (patient_user.id, "vital_alert", "Vitals Alert", "Your blood pressure reading was higher than normal."),
                (doctor_user.id, "alert", "Patient Alert", "Patient Demo Patient has elevated blood pressure."),
                (doctor_user.id, "appointment", "New Appointment", "New appointment scheduled with Demo Patient."),
                (admin_user.id, "system", "System Update", "Backend service restarted successfully."),
                (admin_user.id, "security", "Audit Alert", "Unusual access pattern detected for admin account."),
            ]
            for uid, ntype, title, msg in notifs:
                n = Notification(
                    user_id=uid,
                    type=ntype,
                    title=title,
                    message=msg,
                    channel="in_app",
                )
                db.session.add(n)
            db.session.commit()
            print("Created 8 notifications")

        # === AUDIT LOGS ===
        from app.models.audit_log import AuditLog
        if AuditLog.query.count() == 0:
            import random
            random.seed(99)
            actions = [
                ("view_patient_record", "patient_record"),
                ("view_vitals", "vitals"),
                ("create_appointment", "appointment"),
                ("update_medication", "medication"),
                ("view_report", "medical_report"),
                ("login", "auth"),
                ("export_data", "audit"),
            ]
            for i in range(20):
                action, resource = random.choice(actions)
                log = AuditLog(
                    user_id=random.choice([patient_user.id, doctor_user.id, admin_user.id]),
                    action=action,
                    resource_type=resource,
                    patient_id=patient_user.id,
                    ip_address="10.0.0.1",
                    request_method="GET",
                    request_path=f"/api/v1/{resource}",
                    status_code=200,
                )
                db.session.add(log)
            db.session.commit()
            print("Created 20 audit logs")

        # === SYMPTOM SESSIONS ===
        from app.models.symptom_session import SymptomSession
        if SymptomSession.query.filter_by(patient_id=patient_user.id).count() == 0:
            sessions = [
                ("Persistent headache for 3 days", '{"headache": "throbbing", "duration": "3 days", "severity": 6}',
                 "semi_urgent", "Schedule appointment with doctor. Monitor for worsening symptoms.", "completed"),
                ("Sore throat and mild fever", '{"sore_throat": true, "fever": "37.8C", "cough": "dry"}',
                 "non_urgent", "Rest, fluids, and OTC pain relief. See doctor if symptoms worsen after 5 days.", "completed"),
            ]
            for complaint, symptoms, triage, action, status in sessions:
                s = SymptomSession(
                    patient_id=patient_user.id,
                    chief_complaint=complaint,
                    status=status,
                    triage_level=triage,
                    recommended_action=action,
                    completed_at=utcnow() - timedelta(days=3),
                )
                db.session.add(s)
            db.session.commit()
            print("Created 2 symptom sessions")

        # === CONVERSATIONS ===
        from app.models.conversation import Conversation
        if Conversation.query.filter_by(patient_id=patient_user.id).count() == 0:
            c = Conversation(
                patient_id=patient_user.id,
                agent_type="symptom_analyst",
                title="Headache Assessment",
                status="closed",
            )
            db.session.add(c)
            db.session.commit()
            print("Created 1 conversation")

        print("\n=== SEED COMPLETE ===")
        # Final counts
        from sqlalchemy import text
        tables = ['users', 'patient_profiles', 'doctor_profiles', 'medical_history', 'allergies',
                  'vitals_readings', 'medications', 'medical_reports', 'lab_values', 'appointments',
                  'care_plans', 'care_plan_goals', 'care_plan_activities', 'monitoring_alerts',
                  'notifications', 'audit_logs', 'symptom_sessions', 'conversations']
        total = 0
        for t in tables:
            r = db.session.execute(text(f"SELECT count(*) FROM {t}"))
            c = r.scalar()
            total += c
            print(f"  {t}: {c}")
        print(f"\n  TOTAL: {total} records")


if __name__ == "__main__":
    seed()
