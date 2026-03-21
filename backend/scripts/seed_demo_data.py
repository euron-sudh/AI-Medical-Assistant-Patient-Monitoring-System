"""Seed the database with realistic demo data for MedAssist AI.

This script is idempotent — it checks for existing demo data before inserting.
All seeded users share the password: Demo1234!

Usage:
    DATABASE_URL="postgresql://medassist:medassist_dev@localhost:5499/medassist" python scripts/seed_demo_data.py
"""

import os
import sys
import uuid
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import PatientProfile, MedicalHistory, Allergy
from app.models.doctor import DoctorProfile
from app.models.vitals import VitalsReading
from app.models.report import MedicalReport, LabValue
from app.models.medication import Medication
from app.models.appointment import Appointment
from app.models.care_plan import CarePlan, CarePlanGoal, CarePlanActivity
from app.models.alert import MonitoringAlert
from app.models.symptom_session import SymptomSession
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.conversation import Conversation

# ---------------------------------------------------------------------------
# Constants & data pools
# ---------------------------------------------------------------------------

PASSWORD = "Demo1234!"

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
    "Anthony", "Betty", "Mark", "Margaret", "Donald", "Sandra", "Steven", "Ashley",
    "Paul", "Dorothy", "Andrew", "Kimberly", "Joshua", "Emily",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
]

SPECIALIZATIONS = [
    "Cardiology", "Internal Medicine", "Neurology", "Orthopedics", "Pediatrics",
    "Dermatology", "Oncology", "Endocrinology", "Gastroenterology", "Pulmonology",
]

DEPARTMENTS = [
    "Emergency Medicine", "Internal Medicine", "Surgery", "Cardiology",
    "Neurology", "Pediatrics", "Oncology", "Radiology", "Pathology", "Psychiatry",
]

CONDITIONS = [
    ("Hypertension", "I10", "chronic"),
    ("Type 2 Diabetes Mellitus", "E11.9", "chronic"),
    ("Asthma", "J45.909", "managed"),
    ("Major Depressive Disorder", "F32.9", "active"),
    ("Hyperlipidemia", "E78.5", "chronic"),
    ("Osteoarthritis", "M19.90", "chronic"),
    ("Gastroesophageal Reflux Disease", "K21.0", "managed"),
    ("Chronic Kidney Disease, Stage 3", "N18.3", "chronic"),
    ("Atrial Fibrillation", "I48.91", "active"),
    ("Hypothyroidism", "E03.9", "managed"),
    ("Migraine without Aura", "G43.909", "active"),
    ("Iron Deficiency Anemia", "D50.9", "active"),
    ("Obstructive Sleep Apnea", "G47.33", "managed"),
    ("Chronic Low Back Pain", "M54.5", "chronic"),
    ("Anxiety Disorder", "F41.1", "active"),
]

ALLERGENS = [
    ("Penicillin", "Anaphylaxis, hives", "severe"),
    ("Sulfonamides", "Skin rash, itching", "moderate"),
    ("Aspirin", "Bronchospasm", "severe"),
    ("Latex", "Contact dermatitis", "mild"),
    ("Iodine Contrast", "Hives, swelling", "moderate"),
    ("Codeine", "Nausea, vomiting", "mild"),
    ("Peanuts", "Anaphylaxis", "life_threatening"),
    ("Shellfish", "Hives, swelling", "moderate"),
    ("Bee Stings", "Local swelling", "mild"),
    ("Amoxicillin", "Rash", "moderate"),
]

MEDICATIONS_LIST = [
    ("Lisinopril", "10 mg", "Once daily", "oral", "Hypertension management"),
    ("Metformin", "500 mg", "Twice daily", "oral", "Type 2 diabetes management"),
    ("Atorvastatin", "20 mg", "Once daily at bedtime", "oral", "Hyperlipidemia"),
    ("Amlodipine", "5 mg", "Once daily", "oral", "Hypertension"),
    ("Omeprazole", "20 mg", "Once daily before breakfast", "oral", "GERD"),
    ("Levothyroxine", "50 mcg", "Once daily on empty stomach", "oral", "Hypothyroidism"),
    ("Metoprolol", "25 mg", "Twice daily", "oral", "Heart rate control"),
    ("Gabapentin", "300 mg", "Three times daily", "oral", "Neuropathic pain"),
    ("Sertraline", "50 mg", "Once daily", "oral", "Depression/anxiety"),
    ("Albuterol", "2 puffs", "As needed", "inhalation", "Asthma relief"),
    ("Losartan", "50 mg", "Once daily", "oral", "Hypertension"),
    ("Pantoprazole", "40 mg", "Once daily", "oral", "Acid reflux"),
    ("Hydrochlorothiazide", "25 mg", "Once daily", "oral", "Hypertension"),
    ("Prednisone", "10 mg", "Once daily for 7 days", "oral", "Inflammation"),
    ("Warfarin", "5 mg", "Once daily", "oral", "Atrial fibrillation"),
    ("Insulin Glargine", "20 units", "Once daily at bedtime", "subcutaneous", "Diabetes"),
    ("Clopidogrel", "75 mg", "Once daily", "oral", "Antiplatelet therapy"),
    ("Furosemide", "40 mg", "Once daily", "oral", "Fluid retention"),
    ("Tramadol", "50 mg", "Every 6 hours as needed", "oral", "Pain management"),
    ("Montelukast", "10 mg", "Once daily at bedtime", "oral", "Asthma prevention"),
]

LAB_TESTS = [
    ("Hemoglobin", "g/dL", 12.0, 17.5, "718-7"),
    ("White Blood Cell Count", "10^3/uL", 4.5, 11.0, "6690-2"),
    ("Platelet Count", "10^3/uL", 150.0, 400.0, "777-3"),
    ("Glucose, Fasting", "mg/dL", 70.0, 100.0, "1558-6"),
    ("HbA1c", "%", 4.0, 5.6, "4548-4"),
    ("Total Cholesterol", "mg/dL", 0.0, 200.0, "2093-3"),
    ("LDL Cholesterol", "mg/dL", 0.0, 100.0, "2089-1"),
    ("HDL Cholesterol", "mg/dL", 40.0, 60.0, "2085-9"),
    ("Triglycerides", "mg/dL", 0.0, 150.0, "2571-8"),
    ("Creatinine", "mg/dL", 0.7, 1.3, "2160-0"),
    ("BUN", "mg/dL", 7.0, 20.0, "3094-0"),
    ("Sodium", "mEq/L", 136.0, 145.0, "2951-2"),
    ("Potassium", "mEq/L", 3.5, 5.0, "2823-3"),
    ("ALT", "U/L", 7.0, 56.0, "1742-6"),
    ("AST", "U/L", 10.0, 40.0, "1920-8"),
    ("TSH", "mIU/L", 0.27, 4.2, "3016-3"),
]

CHIEF_COMPLAINTS = [
    "Persistent headache for 3 days",
    "Chest pain when climbing stairs",
    "Shortness of breath at rest",
    "Severe lower back pain",
    "Persistent cough with phlegm for 2 weeks",
    "Dizziness and lightheadedness",
    "Abdominal pain after eating",
    "Numbness and tingling in hands",
    "Fatigue and weakness for past month",
    "Joint pain and stiffness in knees",
]

ALERT_TYPES = [
    ("heart_rate", "Elevated Heart Rate", "Heart rate above normal threshold"),
    ("blood_pressure", "High Blood Pressure", "Systolic BP above 140 mmHg"),
    ("oxygen_saturation", "Low SpO2", "Oxygen saturation below 92%"),
    ("temperature", "Elevated Temperature", "Body temperature above 38.5°C"),
    ("respiratory_rate", "Abnormal Respiratory Rate", "Respiratory rate outside normal range"),
    ("blood_glucose", "High Blood Glucose", "Blood glucose above 200 mg/dL"),
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def random_past_datetime(days_back: int = 90) -> datetime:
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return now_utc() - delta


def random_future_datetime(days_ahead: int = 30) -> datetime:
    delta = timedelta(
        days=random.randint(1, days_ahead),
        hours=random.randint(8, 17),
        minutes=random.choice([0, 15, 30, 45]),
    )
    return now_utc() + delta


def random_past_date(days_back: int = 365) -> date:
    return date.today() - timedelta(days=random.randint(0, days_back))


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_users(existing_emails: set[str]) -> tuple[list, list, list, list]:
    """Create users: 20 patients, 10 doctors, 5 nurses, 2 admins."""
    patients = []
    doctors = []
    nurses = []
    admins = []

    used_emails = set(existing_emails)

    def make_email(first: str, last: str, role: str) -> str:
        base = f"{first.lower()}.{last.lower()}.{role}@demo.medassist.ai"
        if base not in used_emails:
            used_emails.add(base)
            return base
        # add a suffix
        for i in range(1, 100):
            candidate = f"{first.lower()}.{last.lower()}{i}.{role}@demo.medassist.ai"
            if candidate not in used_emails:
                used_emails.add(candidate)
                return candidate
        return f"{uuid.uuid4().hex[:8]}.{role}@demo.medassist.ai"

    # 20 patients
    for i in range(20):
        fn = FIRST_NAMES[i % len(FIRST_NAMES)]
        ln = LAST_NAMES[i % len(LAST_NAMES)]
        user = User(
            email=make_email(fn, ln, "patient"),
            role="patient",
            first_name=fn,
            last_name=ln,
            phone=f"+1555{random.randint(1000000, 9999999)}",
            is_active=True,
            is_verified=True,
        )
        user.set_password(PASSWORD)
        patients.append(user)

    # 10 doctors
    for i in range(10):
        fn = FIRST_NAMES[(i + 20) % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i + 20) % len(LAST_NAMES)]
        user = User(
            email=make_email(fn, ln, "doctor"),
            role="doctor",
            first_name=fn,
            last_name=ln,
            phone=f"+1555{random.randint(1000000, 9999999)}",
            is_active=True,
            is_verified=True,
        )
        user.set_password(PASSWORD)
        doctors.append(user)

    # 5 nurses
    for i in range(5):
        fn = FIRST_NAMES[(i + 30) % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i + 10) % len(LAST_NAMES)]
        user = User(
            email=make_email(fn, ln, "nurse"),
            role="nurse",
            first_name=fn,
            last_name=ln,
            phone=f"+1555{random.randint(1000000, 9999999)}",
            is_active=True,
            is_verified=True,
        )
        user.set_password(PASSWORD)
        nurses.append(user)

    # 2 admins
    for i in range(2):
        fn = FIRST_NAMES[(i + 35) % len(FIRST_NAMES)]
        ln = LAST_NAMES[(i + 25) % len(LAST_NAMES)]
        user = User(
            email=make_email(fn, ln, "admin"),
            role="admin",
            first_name=fn,
            last_name=ln,
            phone=f"+1555{random.randint(1000000, 9999999)}",
            is_active=True,
            is_verified=True,
        )
        user.set_password(PASSWORD)
        admins.append(user)

    all_users = patients + doctors + nurses + admins
    db.session.add_all(all_users)
    db.session.flush()  # Get IDs assigned

    return patients, doctors, nurses, admins


def seed_patient_profiles(patients: list, doctors: list) -> list:
    """Create patient profiles with demographics."""
    profiles = []
    genders = ["Male", "Female", "Non-binary"]
    blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

    for i, patient in enumerate(patients):
        profile = PatientProfile(
            user_id=patient.id,
            date_of_birth=date(
                random.randint(1945, 2005),
                random.randint(1, 12),
                random.randint(1, 28),
            ),
            gender=random.choice(genders),
            blood_type=random.choice(blood_types),
            height_cm=Decimal(str(random.randint(150, 195))),
            weight_kg=Decimal(str(random.randint(50, 120))),
            emergency_contact={
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "phone": f"+1555{random.randint(1000000, 9999999)}",
                "relationship": random.choice(["Spouse", "Parent", "Sibling", "Child"]),
            },
            insurance_info={
                "provider": random.choice(["Blue Cross", "Aetna", "UnitedHealth", "Cigna", "Kaiser"]),
                "policy_number": f"POL-{random.randint(100000, 999999)}",
                "group_number": f"GRP-{random.randint(1000, 9999)}",
            },
            assigned_doctor_id=doctors[i % len(doctors)].id,
        )
        profiles.append(profile)

    db.session.add_all(profiles)
    db.session.flush()
    return profiles


def seed_medical_history(profiles: list, doctors: list) -> list:
    """Create medical history entries for patients."""
    entries = []
    for profile in profiles:
        # Each patient gets 1-3 conditions
        num_conditions = random.randint(1, 3)
        chosen = random.sample(CONDITIONS, min(num_conditions, len(CONDITIONS)))
        for condition_name, icd10, status in chosen:
            entry = MedicalHistory(
                patient_id=profile.id,
                condition_name=condition_name,
                diagnosis_date=random_past_date(days_back=3650),
                status=status,
                icd_10_code=icd10,
                notes=f"Patient diagnosed with {condition_name}. Ongoing management.",
                diagnosed_by=random.choice(doctors).id,
                created_by=random.choice(doctors).id,
            )
            entries.append(entry)

    db.session.add_all(entries)
    db.session.flush()
    return entries


def seed_allergies(profiles: list, doctors: list) -> list:
    """Create allergy records for patients."""
    entries = []
    for profile in profiles:
        if random.random() < 0.6:  # 60% of patients have allergies
            num = random.randint(1, 2)
            chosen = random.sample(ALLERGENS, min(num, len(ALLERGENS)))
            for allergen, reaction, severity in chosen:
                entry = Allergy(
                    patient_id=profile.id,
                    allergen=allergen,
                    reaction=reaction,
                    severity=severity,
                    diagnosed_date=random_past_date(days_back=3650),
                    created_by=random.choice(doctors).id,
                )
                entries.append(entry)

    db.session.add_all(entries)
    db.session.flush()
    return entries


def seed_doctor_profiles(doctors: list) -> list:
    """Create doctor profiles with specializations."""
    profiles = []
    states = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]

    for i, doctor in enumerate(doctors):
        profile = DoctorProfile(
            user_id=doctor.id,
            specialization=SPECIALIZATIONS[i % len(SPECIALIZATIONS)],
            license_number=f"MD-{random.randint(100000, 999999)}",
            license_state=states[i % len(states)],
            years_of_experience=random.randint(3, 30),
            department=DEPARTMENTS[i % len(DEPARTMENTS)],
            consultation_fee=Decimal(str(random.randint(100, 500))),
            bio=f"Board-certified {SPECIALIZATIONS[i % len(SPECIALIZATIONS)].lower()} specialist "
                f"with {random.randint(5, 25)} years of clinical experience.",
            availability={
                "monday": ["09:00-12:00", "14:00-17:00"],
                "tuesday": ["09:00-12:00", "14:00-17:00"],
                "wednesday": ["09:00-12:00"],
                "thursday": ["09:00-12:00", "14:00-17:00"],
                "friday": ["09:00-12:00", "14:00-16:00"],
            },
        )
        profiles.append(profile)

    db.session.add_all(profiles)
    db.session.flush()
    return profiles


def seed_vitals(patients: list) -> list:
    """Create 100 vitals readings spread across patients."""
    readings = []
    for _ in range(100):
        patient = random.choice(patients)
        is_anomalous = random.random() < 0.15  # 15% anomalous

        if is_anomalous:
            hr = random.randint(110, 160)
            sys_bp = random.randint(145, 200)
            dia_bp = random.randint(92, 120)
            spo2 = Decimal(str(round(random.uniform(85.0, 93.0), 2)))
            temp = Decimal(str(round(random.uniform(38.5, 40.0), 2)))
            rr = random.randint(22, 35)
        else:
            hr = random.randint(60, 100)
            sys_bp = random.randint(110, 135)
            dia_bp = random.randint(65, 85)
            spo2 = Decimal(str(round(random.uniform(95.0, 100.0), 2)))
            temp = Decimal(str(round(random.uniform(36.2, 37.2), 2)))
            rr = random.randint(12, 20)

        reading = VitalsReading(
            patient_id=patient.id,
            heart_rate=hr,
            blood_pressure_systolic=sys_bp,
            blood_pressure_diastolic=dia_bp,
            temperature=temp,
            oxygen_saturation=spo2,
            respiratory_rate=rr,
            blood_glucose=Decimal(str(random.randint(70, 180))),
            weight_kg=Decimal(str(round(random.uniform(50.0, 120.0), 1))),
            pain_level=random.randint(0, 7),
            is_manual_entry=random.choice([True, False]),
            is_anomalous=is_anomalous,
            notes="Routine vitals check" if not is_anomalous else "Abnormal reading flagged for review",
            recorded_at=random_past_datetime(days_back=60),
            created_by=patient.id,
        )
        readings.append(reading)

    db.session.add_all(readings)
    db.session.flush()
    return readings


def seed_reports_and_labs(patients: list, doctors: list) -> tuple[list, list]:
    """Create 50 medical reports with lab values."""
    reports = []
    lab_values = []
    report_types = ["lab", "imaging", "pathology", "radiology", "consultation", "progress"]
    statuses = ["pending", "completed", "reviewed"]

    for _ in range(50):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        rtype = random.choice(report_types)
        status = random.choice(statuses)

        report = MedicalReport(
            patient_id=patient.id,
            report_type=rtype,
            title=f"{rtype.title()} Report - {random_past_date(30).strftime('%B %d, %Y')}",
            content=f"Clinical {rtype} report for patient. Findings are within expected parameters."
                    if rtype != "lab" else None,
            file_url=f"https://storage.medassist.ai/reports/{uuid.uuid4()}.pdf",
            file_type="application/pdf",
            ai_summary=f"AI analysis of {rtype} report: No significant abnormalities detected."
                       if status in ("completed", "reviewed") else None,
            ai_analysis={"confidence": 0.92, "findings": ["Normal"]}
                        if status in ("completed", "reviewed") else None,
            status=status,
            reviewed_by=doctor.id if status == "reviewed" else None,
            reviewed_at=random_past_datetime(15) if status == "reviewed" else None,
            created_by=patient.id,
            created_at=random_past_datetime(60),
        )
        reports.append(report)
        db.session.add(report)
        db.session.flush()

        # Add lab values for lab reports
        if rtype == "lab":
            num_tests = random.randint(3, 8)
            chosen_tests = random.sample(LAB_TESTS, min(num_tests, len(LAB_TESTS)))
            for test_name, unit, ref_min, ref_max, loinc in chosen_tests:
                # Generate value - sometimes abnormal
                if random.random() < 0.2:
                    value = round(random.uniform(ref_min * 0.6, ref_max * 1.4), 4)
                else:
                    value = round(random.uniform(ref_min, ref_max), 4)

                is_abnormal = value < ref_min or value > ref_max

                lv = LabValue(
                    report_id=report.id,
                    patient_id=patient.id,
                    test_name=test_name,
                    value=Decimal(str(value)),
                    unit=unit,
                    reference_min=Decimal(str(ref_min)),
                    reference_max=Decimal(str(ref_max)),
                    is_abnormal=is_abnormal,
                    loinc_code=loinc,
                    collected_at=random_past_datetime(60),
                )
                lab_values.append(lv)

    db.session.add_all(lab_values)
    db.session.flush()
    return reports, lab_values


def seed_appointments(patients: list, doctors: list) -> list:
    """Create 30 appointments with mixed statuses."""
    appointments = []
    types = ["in_person", "telemedicine", "follow_up"]
    reasons = [
        "Annual physical examination",
        "Follow-up for hypertension management",
        "Lab results review",
        "Chest pain evaluation",
        "Diabetes management consultation",
        "Post-surgical follow-up",
        "Medication adjustment",
        "Persistent headache evaluation",
        "Respiratory complaint",
        "Joint pain assessment",
    ]

    for i in range(30):
        patient = random.choice(patients)
        doctor = random.choice(doctors)

        if i < 10:
            # Future scheduled
            sched = random_future_datetime(30)
            status = random.choice(["scheduled", "confirmed"])
        elif i < 20:
            # Past completed
            sched = random_past_datetime(60)
            status = "completed"
        elif i < 25:
            # Past cancelled
            sched = random_past_datetime(30)
            status = "cancelled"
        else:
            # Past no-show
            sched = random_past_datetime(45)
            status = random.choice(["no_show", "completed"])

        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_type=random.choice(types),
            status=status,
            scheduled_at=sched,
            duration_minutes=random.choice([15, 30, 45, 60]),
            reason=random.choice(reasons),
            notes="Patient requires follow-up." if status == "completed" else None,
            cancelled_by=patient.id if status == "cancelled" else None,
            cancelled_reason="Schedule conflict" if status == "cancelled" else None,
            created_by=patient.id,
        )
        appointments.append(appt)

    db.session.add_all(appointments)
    db.session.flush()
    return appointments


def seed_medications(patients: list, doctors: list) -> list:
    """Create 20 medications spread across patients."""
    meds = []
    statuses = ["active", "active", "active", "completed", "discontinued"]

    for _ in range(20):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        med_data = random.choice(MEDICATIONS_LIST)
        name, dosage, frequency, route, reason = med_data
        status = random.choice(statuses)

        med = Medication(
            patient_id=patient.id,
            name=name,
            dosage=dosage,
            frequency=frequency,
            route=route,
            prescribed_by=doctor.id,
            start_date=random_past_date(180),
            end_date=random_past_date(10) if status in ("completed", "discontinued") else None,
            status=status,
            reason=reason,
            side_effects=None,
            refills_remaining=random.randint(0, 5) if status == "active" else 0,
            pharmacy_notes=None,
            created_by=doctor.id,
        )
        meds.append(med)

    db.session.add_all(meds)
    db.session.flush()
    return meds


def seed_care_plans(patients: list, doctors: list) -> tuple[list, list, list]:
    """Create 15 care plans with goals and activities."""
    plans = []
    goals = []
    activities = []

    plan_titles = [
        "Hypertension Management Plan",
        "Diabetes Type 2 Control Plan",
        "Post-Surgical Recovery Plan",
        "Weight Management Program",
        "Cardiac Rehabilitation",
        "Chronic Pain Management",
        "Asthma Action Plan",
        "Mental Health Wellness Plan",
        "Osteoarthritis Management",
        "Cholesterol Reduction Plan",
        "Sleep Improvement Plan",
        "Anxiety Management Program",
        "Post-COVID Recovery",
        "Kidney Health Monitoring",
        "Thyroid Management Plan",
    ]

    goal_titles = [
        ("Reduce blood pressure to 120/80", "120/80", "mmHg"),
        ("Lower HbA1c to below 7%", "7.0", "%"),
        ("Walk 30 minutes daily", "30", "min/day"),
        ("Lose 10 pounds in 3 months", "10", "lbs"),
        ("Reduce resting heart rate to 70 bpm", "70", "bpm"),
        ("Improve sleep quality score to 8/10", "8", "score"),
        ("Reduce pain level to 3 or below", "3", "pain scale"),
        ("Lower total cholesterol to 180", "180", "mg/dL"),
    ]

    activity_types = ["medication", "exercise", "diet", "monitoring", "appointment", "other"]

    for i in range(15):
        patient = random.choice(patients)
        doctor = random.choice(doctors)
        status = random.choice(["active", "active", "draft", "completed"])

        plan = CarePlan(
            patient_id=patient.id,
            doctor_id=doctor.id,
            title=plan_titles[i % len(plan_titles)],
            description=f"Personalized care plan for {patient.first_name}. "
                        f"Follow-up in 4 weeks.",
            status=status,
            start_date=random_past_date(90),
            end_date=date.today() + timedelta(days=random.randint(30, 180)),
            ai_recommendations={
                "lifestyle": ["Regular exercise", "Balanced diet", "Adequate sleep"],
                "monitoring": ["Weekly vitals check", "Monthly lab work"],
            },
            created_by=doctor.id,
        )
        plans.append(plan)
        db.session.add(plan)
        db.session.flush()

        # 2-3 goals per plan
        for j in range(random.randint(2, 3)):
            gt = goal_titles[j % len(goal_titles)]
            try:
                current_val = str(round(float(gt[1]) * random.uniform(0.8, 1.2), 1))
            except ValueError:
                current_val = gt[1]  # non-numeric like "120/80"

            goal = CarePlanGoal(
                care_plan_id=plan.id,
                title=gt[0],
                description=f"Target: achieve {gt[0].lower()}",
                target_value=gt[1],
                current_value=current_val,
                unit=gt[2],
                status=random.choice(["not_started", "in_progress", "in_progress", "achieved"]),
                target_date=date.today() + timedelta(days=random.randint(14, 90)),
            )
            goals.append(goal)
            db.session.add(goal)
            db.session.flush()

            # 1-2 activities per goal
            for _ in range(random.randint(1, 2)):
                activity = CarePlanActivity(
                    care_plan_id=plan.id,
                    goal_id=goal.id,
                    title=f"{random.choice(['Take', 'Complete', 'Perform', 'Monitor'])} "
                          f"{random.choice(['medication', 'exercise routine', 'blood pressure check', 'blood glucose test'])}",
                    description="Follow prescribed schedule consistently.",
                    activity_type=random.choice(activity_types),
                    frequency=random.choice(["Daily", "Twice daily", "Weekly", "As needed"]),
                    status=random.choice(["pending", "in_progress", "completed"]),
                    due_date=random_future_datetime(30) if random.random() > 0.3 else None,
                    completed_at=random_past_datetime(7) if random.random() < 0.3 else None,
                )
                activities.append(activity)

    db.session.add_all(activities)
    db.session.flush()
    return plans, goals, activities


def seed_alerts(patients: list, vitals_readings: list) -> list:
    """Create 10 monitoring alerts."""
    alerts = []
    severities = ["low", "medium", "high", "critical"]
    statuses = ["active", "active", "acknowledged", "resolved"]

    for _ in range(10):
        patient = random.choice(patients)
        alert_data = random.choice(ALERT_TYPES)
        atype, title, desc = alert_data
        severity = random.choice(severities)
        status = random.choice(statuses)

        # Link to a vitals reading if possible
        patient_readings = [r for r in vitals_readings if r.patient_id == patient.id]
        vitals_id = patient_readings[0].id if patient_readings else None

        alert = MonitoringAlert(
            patient_id=patient.id,
            vitals_reading_id=vitals_id,
            alert_type=atype,
            severity=severity,
            title=title,
            description=desc,
            ai_analysis={"recommendation": "Monitor closely", "confidence": 0.87},
            status=status,
            escalation_level=random.randint(0, 2),
            created_at=random_past_datetime(14),
        )
        alerts.append(alert)

    db.session.add_all(alerts)
    db.session.flush()
    return alerts


def seed_symptom_sessions(patients: list) -> list:
    """Create 10 symptom sessions."""
    sessions = []
    statuses = ["completed", "completed", "in_progress", "cancelled"]
    triage_levels = ["non_urgent", "semi_urgent", "urgent", "emergency"]

    for i in range(10):
        patient = random.choice(patients)
        status = random.choice(statuses)
        complaint = CHIEF_COMPLAINTS[i % len(CHIEF_COMPLAINTS)]

        session = SymptomSession(
            patient_id=patient.id,
            status=status,
            chief_complaint=complaint,
            symptoms={
                "reported": [complaint],
                "severity": random.randint(3, 8),
                "duration": f"{random.randint(1, 14)} days",
            },
            ai_analysis={
                "differential_diagnoses": [
                    {"condition": "Tension headache", "confidence": 0.78},
                    {"condition": "Migraine", "confidence": 0.65},
                ],
                "urgency_score": random.randint(2, 8),
            } if status == "completed" else None,
            triage_level=random.choice(triage_levels) if status == "completed" else None,
            recommended_action="Schedule appointment with primary care physician"
                              if status == "completed" else None,
            conversation_log={
                "messages": [
                    {"role": "user", "content": complaint},
                    {"role": "assistant", "content": "I understand. Can you describe the severity on a scale of 1-10?"},
                    {"role": "user", "content": f"About a {random.randint(4, 8)}"},
                ]
            },
            completed_at=random_past_datetime(7) if status == "completed" else None,
            created_at=random_past_datetime(30),
        )
        sessions.append(session)

    db.session.add_all(sessions)
    db.session.flush()
    return sessions


def seed_notifications(all_users: list) -> list:
    """Create 20 notifications."""
    notifications = []
    types_and_messages = [
        ("appointment_reminder", "Appointment Reminder", "You have an upcoming appointment tomorrow at 10:00 AM."),
        ("medication_reminder", "Medication Reminder", "Time to take your Lisinopril 10 mg."),
        ("report_ready", "Report Available", "Your lab results are now available for review."),
        ("alert", "Vital Alert", "Your heart rate reading was above normal range."),
        ("care_plan_update", "Care Plan Updated", "Your doctor has updated your care plan."),
        ("system", "Welcome", "Welcome to MedAssist AI. Complete your profile to get started."),
        ("appointment_confirmation", "Appointment Confirmed", "Your appointment has been confirmed."),
        ("message", "New Message", "You have a new message from your care team."),
    ]

    for i in range(20):
        user = random.choice(all_users)
        ntype, title, message = random.choice(types_and_messages)
        is_read = random.random() < 0.4

        notif = Notification(
            user_id=user.id,
            type=ntype,
            title=title,
            message=message,
            data={"source": "system"},
            read=is_read,
            read_at=random_past_datetime(2) if is_read else None,
            channel=random.choice(["in_app", "email", "push"]),
            sent_at=random_past_datetime(7),
            created_at=random_past_datetime(7),
        )
        notifications.append(notif)

    db.session.add_all(notifications)
    db.session.flush()
    return notifications


def seed_audit_logs(all_users: list, patients: list) -> list:
    """Create 50 audit log entries."""
    logs = []
    actions = [
        ("view_patient_record", "patient_record"),
        ("view_vitals", "vitals_reading"),
        ("create_vitals", "vitals_reading"),
        ("view_report", "medical_report"),
        ("upload_report", "medical_report"),
        ("view_medications", "medication"),
        ("create_prescription", "medication"),
        ("view_care_plan", "care_plan"),
        ("login", "auth"),
        ("logout", "auth"),
        ("view_appointment", "appointment"),
        ("create_appointment", "appointment"),
        ("view_audit_logs", "audit_log"),
        ("export_data", "patient_record"),
    ]
    methods = ["GET", "POST", "PUT", "DELETE"]
    ips = ["192.168.1.100", "10.0.0.50", "172.16.0.25", "192.168.1.150", "10.0.0.75"]

    for _ in range(50):
        user = random.choice(all_users)
        action, resource_type = random.choice(actions)
        patient = random.choice(patients) if resource_type != "auth" else None

        log = AuditLog(
            user_id=user.id,
            action=action,
            resource_type=resource_type,
            resource_id=uuid.uuid4() if resource_type != "auth" else None,
            patient_id=patient.id if patient else None,
            ip_address=random.choice(ips),
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            request_method=random.choice(methods),
            request_path=f"/api/v1/{resource_type.replace('_', '-')}s",
            status_code=random.choice([200, 200, 200, 201, 403]),
            details={"description": f"User performed {action}"},
            created_at=random_past_datetime(30),
        )
        logs.append(log)

    db.session.add_all(logs)
    db.session.flush()
    return logs


def seed_conversations(patients: list) -> list:
    """Create 10 conversations."""
    conversations = []
    agent_types = ["symptom_analyst", "general", "drug_interaction", "follow_up", "report_reader"]
    statuses = ["active", "closed", "closed", "closed"]

    titles = [
        "Headache symptoms discussion",
        "Medication questions",
        "Lab results review",
        "Follow-up care discussion",
        "Chest pain evaluation",
        "Diet and exercise guidance",
        "Blood pressure concerns",
        "Sleep quality issues",
        "Prescription refill request",
        "Post-surgery recovery questions",
    ]

    for i in range(10):
        patient = random.choice(patients)
        agent = random.choice(agent_types)

        conv = Conversation(
            patient_id=patient.id,
            agent_type=agent,
            title=titles[i],
            messages=[
                {"role": "user", "content": f"I have a question about {titles[i].lower()}."},
                {"role": "assistant", "content": "I'd be happy to help. Could you provide more details?"},
                {"role": "user", "content": "I've been experiencing this for about a week now."},
                {"role": "assistant", "content": "Based on what you've described, I recommend consulting with your physician. Would you like me to help schedule an appointment?"},
            ],
            status=random.choice(statuses),
            metadata_={"agent_model": "gpt-4o", "tokens_used": random.randint(500, 2000)},
            created_at=random_past_datetime(30),
        )
        conversations.append(conv)

    db.session.add_all(conversations)
    db.session.flush()
    return conversations


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Run the seed script."""
    app = create_app("development")

    with app.app_context():
        # Check if demo data already exists
        existing_count = db.session.query(User).filter(
            User.email.like("%@demo.medassist.ai")
        ).count()

        if existing_count > 0:
            print(f"Found {existing_count} existing demo users. Deleting old demo data...")
            # Clean up old demo data in reverse dependency order
            demo_users = db.session.query(User).filter(
                User.email.like("%@demo.medassist.ai")
            ).all()
            demo_ids = [u.id for u in demo_users]

            if demo_ids:
                # Delete in dependency order
                db.session.query(Conversation).filter(Conversation.patient_id.in_(demo_ids)).delete(synchronize_session=False)
                db.session.query(AuditLog).filter(AuditLog.user_id.in_(demo_ids)).delete(synchronize_session=False)
                db.session.query(Notification).filter(Notification.user_id.in_(demo_ids)).delete(synchronize_session=False)
                db.session.query(SymptomSession).filter(SymptomSession.patient_id.in_(demo_ids)).delete(synchronize_session=False)
                db.session.query(MonitoringAlert).filter(MonitoringAlert.patient_id.in_(demo_ids)).delete(synchronize_session=False)

                # Care plan cleanup
                care_plans = db.session.query(CarePlan).filter(CarePlan.patient_id.in_(demo_ids)).all()
                cp_ids = [cp.id for cp in care_plans]
                if cp_ids:
                    db.session.query(CarePlanActivity).filter(CarePlanActivity.care_plan_id.in_(cp_ids)).delete(synchronize_session=False)
                    db.session.query(CarePlanGoal).filter(CarePlanGoal.care_plan_id.in_(cp_ids)).delete(synchronize_session=False)
                    db.session.query(CarePlan).filter(CarePlan.id.in_(cp_ids)).delete(synchronize_session=False)

                db.session.query(Medication).filter(Medication.patient_id.in_(demo_ids)).delete(synchronize_session=False)

                # Appointments and telemedicine
                from app.models.telemedicine import TelemedicineSession
                appts = db.session.query(Appointment).filter(Appointment.patient_id.in_(demo_ids)).all()
                appt_ids = [a.id for a in appts]
                if appt_ids:
                    db.session.query(TelemedicineSession).filter(TelemedicineSession.appointment_id.in_(appt_ids)).delete(synchronize_session=False)
                db.session.query(Appointment).filter(Appointment.patient_id.in_(demo_ids)).delete(synchronize_session=False)

                # Reports and lab values
                reports = db.session.query(MedicalReport).filter(MedicalReport.patient_id.in_(demo_ids)).all()
                report_ids = [r.id for r in reports]
                if report_ids:
                    db.session.query(LabValue).filter(LabValue.report_id.in_(report_ids)).delete(synchronize_session=False)
                db.session.query(MedicalReport).filter(MedicalReport.patient_id.in_(demo_ids)).delete(synchronize_session=False)

                db.session.query(VitalsReading).filter(VitalsReading.patient_id.in_(demo_ids)).delete(synchronize_session=False)

                # Patient profiles (cascades medical history and allergies)
                profiles = db.session.query(PatientProfile).filter(PatientProfile.user_id.in_(demo_ids)).all()
                profile_ids = [p.id for p in profiles]
                if profile_ids:
                    db.session.query(Allergy).filter(Allergy.patient_id.in_(profile_ids)).delete(synchronize_session=False)
                    db.session.query(MedicalHistory).filter(MedicalHistory.patient_id.in_(profile_ids)).delete(synchronize_session=False)
                db.session.query(PatientProfile).filter(PatientProfile.user_id.in_(demo_ids)).delete(synchronize_session=False)
                db.session.query(DoctorProfile).filter(DoctorProfile.user_id.in_(demo_ids)).delete(synchronize_session=False)

                db.session.query(User).filter(User.id.in_(demo_ids)).delete(synchronize_session=False)

                db.session.commit()
                print("Old demo data deleted.")

        # Collect existing emails to avoid conflicts
        existing_emails = {row[0] for row in db.session.query(User.email).all()}

        print("Seeding users...")
        patients, doctors, nurses, admins = seed_users(existing_emails)
        all_users = patients + doctors + nurses + admins

        print("Seeding patient profiles...")
        profiles = seed_patient_profiles(patients, doctors)

        print("Seeding medical history...")
        seed_medical_history(profiles, doctors)

        print("Seeding allergies...")
        seed_allergies(profiles, doctors)

        print("Seeding doctor profiles...")
        seed_doctor_profiles(doctors)

        print("Seeding vitals readings...")
        vitals_readings = seed_vitals(patients)

        print("Seeding medical reports and lab values...")
        seed_reports_and_labs(patients, doctors)

        print("Seeding appointments...")
        seed_appointments(patients, doctors)

        print("Seeding medications...")
        seed_medications(patients, doctors)

        print("Seeding care plans...")
        seed_care_plans(patients, doctors)

        print("Seeding monitoring alerts...")
        seed_alerts(patients, vitals_readings)

        print("Seeding symptom sessions...")
        seed_symptom_sessions(patients)

        print("Seeding notifications...")
        seed_notifications(all_users)

        print("Seeding audit logs...")
        seed_audit_logs(all_users, patients)

        print("Seeding conversations...")
        seed_conversations(patients)

        db.session.commit()

        # Print summary
        print("\n" + "=" * 60)
        print("SEED COMPLETE - Summary:")
        print("=" * 60)
        print(f"  Users:              {db.session.query(User).count()}")
        print(f"  Patient Profiles:   {db.session.query(PatientProfile).count()}")
        print(f"  Doctor Profiles:    {db.session.query(DoctorProfile).count()}")
        print(f"  Medical History:    {db.session.query(MedicalHistory).count()}")
        print(f"  Allergies:          {db.session.query(Allergy).count()}")
        print(f"  Vitals Readings:    {db.session.query(VitalsReading).count()}")
        print(f"  Medical Reports:    {db.session.query(MedicalReport).count()}")
        print(f"  Lab Values:         {db.session.query(LabValue).count()}")
        print(f"  Appointments:       {db.session.query(Appointment).count()}")
        print(f"  Medications:        {db.session.query(Medication).count()}")
        print(f"  Care Plans:         {db.session.query(CarePlan).count()}")
        print(f"  Care Plan Goals:    {db.session.query(CarePlanGoal).count()}")
        print(f"  Care Plan Activities: {db.session.query(CarePlanActivity).count()}")
        print(f"  Monitoring Alerts:  {db.session.query(MonitoringAlert).count()}")
        print(f"  Symptom Sessions:   {db.session.query(SymptomSession).count()}")
        print(f"  Notifications:      {db.session.query(Notification).count()}")
        print(f"  Audit Logs:         {db.session.query(AuditLog).count()}")
        print(f"  Conversations:      {db.session.query(Conversation).count()}")
        print("=" * 60)
        print(f"\nAll demo users have password: {PASSWORD}")
        print("Demo user emails end with: @demo.medassist.ai")
        print("Original test users (patient@demo.dev, etc.) are untouched.")


if __name__ == "__main__":
    main()
