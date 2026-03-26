"""
Comprehensive production seed script.
Creates 10 patients, 5 doctors, 1 admin with full synthetic data
so every page/button in the app has data to display.
"""

import os
import sys
import uuid
import random
import json
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.patient import PatientProfile, MedicalHistory, Allergy
from app.models.doctor import DoctorProfile
from app.models.vitals import VitalsReading
from app.models.appointment import Appointment
from app.models.medication import Medication
from app.models.care_plan import CarePlan, CarePlanGoal, CarePlanActivity
from app.models.notification import Notification
from app.models.report import MedicalReport, LabValue
from app.models.conversation import Conversation
from app.models.symptom_session import SymptomSession
from app.models.alert import MonitoringAlert
from app.models.audit_log import AuditLog

now = datetime.now(timezone.utc)


# ──────────────────────────────────────────────────────────────────────────────
# DATA POOLS
# ──────────────────────────────────────────────────────────────────────────────

PATIENTS = [
    {"first": "Sarah", "last": "Johnson", "email": "sarah.johnson@medassist.ai", "phone": "+1-555-0101",
     "dob": date(1985, 3, 12), "gender": "Female", "blood": "A+", "height": 165, "weight": 62,
     "emergency": {"name": "Mike Johnson", "phone": "+1-555-0102", "relationship": "Spouse"},
     "insurance": {"provider": "BlueCross BlueShield", "policy_number": "BCB-2024-001", "group_number": "GRP-500"}},
    {"first": "James", "last": "Williams", "email": "james.williams@medassist.ai", "phone": "+1-555-0103",
     "dob": date(1978, 7, 25), "gender": "Male", "blood": "O+", "height": 180, "weight": 88,
     "emergency": {"name": "Linda Williams", "phone": "+1-555-0104", "relationship": "Wife"},
     "insurance": {"provider": "Aetna", "policy_number": "AET-2024-045", "group_number": "GRP-210"}},
    {"first": "Maria", "last": "Garcia", "email": "maria.garcia@medassist.ai", "phone": "+1-555-0105",
     "dob": date(1992, 11, 3), "gender": "Female", "blood": "B+", "height": 160, "weight": 55,
     "emergency": {"name": "Carlos Garcia", "phone": "+1-555-0106", "relationship": "Brother"},
     "insurance": {"provider": "Cigna", "policy_number": "CIG-2024-112", "group_number": "GRP-320"}},
    {"first": "Robert", "last": "Chen", "email": "robert.chen@medassist.ai", "phone": "+1-555-0107",
     "dob": date(1965, 1, 18), "gender": "Male", "blood": "AB+", "height": 172, "weight": 79,
     "emergency": {"name": "Mei Chen", "phone": "+1-555-0108", "relationship": "Wife"},
     "insurance": {"provider": "UnitedHealth", "policy_number": "UHC-2024-089", "group_number": "GRP-150"}},
    {"first": "Emily", "last": "Davis", "email": "emily.davis@medassist.ai", "phone": "+1-555-0109",
     "dob": date(1988, 5, 30), "gender": "Female", "blood": "O-", "height": 170, "weight": 68,
     "emergency": {"name": "Tom Davis", "phone": "+1-555-0110", "relationship": "Husband"},
     "insurance": {"provider": "Humana", "policy_number": "HUM-2024-201", "group_number": "GRP-440"}},
    {"first": "Michael", "last": "Brown", "email": "michael.brown@medassist.ai", "phone": "+1-555-0111",
     "dob": date(1972, 9, 8), "gender": "Male", "blood": "A-", "height": 185, "weight": 95,
     "emergency": {"name": "Karen Brown", "phone": "+1-555-0112", "relationship": "Wife"},
     "insurance": {"provider": "Kaiser Permanente", "policy_number": "KP-2024-167", "group_number": "GRP-600"}},
    {"first": "Aisha", "last": "Patel", "email": "aisha.patel@medassist.ai", "phone": "+1-555-0113",
     "dob": date(1995, 4, 22), "gender": "Female", "blood": "B-", "height": 158, "weight": 52,
     "emergency": {"name": "Raj Patel", "phone": "+1-555-0114", "relationship": "Father"},
     "insurance": {"provider": "Anthem", "policy_number": "ANT-2024-334", "group_number": "GRP-780"}},
    {"first": "David", "last": "Kim", "email": "david.kim@medassist.ai", "phone": "+1-555-0115",
     "dob": date(1980, 12, 1), "gender": "Male", "blood": "O+", "height": 175, "weight": 72,
     "emergency": {"name": "Soo Kim", "phone": "+1-555-0116", "relationship": "Wife"},
     "insurance": {"provider": "Molina Healthcare", "policy_number": "MOL-2024-445", "group_number": "GRP-190"}},
    {"first": "Jennifer", "last": "Taylor", "email": "jennifer.taylor@medassist.ai", "phone": "+1-555-0117",
     "dob": date(1990, 8, 14), "gender": "Female", "blood": "AB-", "height": 168, "weight": 64,
     "emergency": {"name": "Mark Taylor", "phone": "+1-555-0118", "relationship": "Husband"},
     "insurance": {"provider": "BlueCross BlueShield", "policy_number": "BCB-2024-556", "group_number": "GRP-500"}},
    {"first": "William", "last": "Anderson", "email": "william.anderson@medassist.ai", "phone": "+1-555-0119",
     "dob": date(1958, 2, 28), "gender": "Male", "blood": "A+", "height": 178, "weight": 85,
     "emergency": {"name": "Patricia Anderson", "phone": "+1-555-0120", "relationship": "Wife"},
     "insurance": {"provider": "Medicare", "policy_number": "MED-2024-901", "group_number": "N/A"}},
]

DOCTORS = [
    {"first": "Dr. Priya", "last": "Sharma", "email": "priya.sharma@medassist.ai", "phone": "+1-555-0201",
     "spec": "Internal Medicine", "license": "MD-NY-28451", "state": "NY", "exp": 15, "dept": "General Medicine",
     "fee": 150, "bio": "Board-certified internist specializing in preventive care and chronic disease management."},
    {"first": "Dr. Thomas", "last": "Mitchell", "email": "thomas.mitchell@medassist.ai", "phone": "+1-555-0202",
     "spec": "Cardiology", "license": "MD-CA-31892", "state": "CA", "exp": 20, "dept": "Cardiology",
     "fee": 250, "bio": "Interventional cardiologist with expertise in heart failure and arrhythmia management."},
    {"first": "Dr. Lisa", "last": "Wong", "email": "lisa.wong@medassist.ai", "phone": "+1-555-0203",
     "spec": "Endocrinology", "license": "MD-TX-45123", "state": "TX", "exp": 12, "dept": "Endocrinology",
     "fee": 200, "bio": "Endocrinologist focused on diabetes management, thyroid disorders, and metabolic health."},
    {"first": "Dr. Ahmed", "last": "Hassan", "email": "ahmed.hassan@medassist.ai", "phone": "+1-555-0204",
     "spec": "Pulmonology", "license": "MD-IL-52789", "state": "IL", "exp": 18, "dept": "Pulmonology",
     "fee": 225, "bio": "Pulmonologist specializing in COPD, asthma, and sleep-disordered breathing."},
    {"first": "Dr. Rachel", "last": "Green", "email": "rachel.green@medassist.ai", "phone": "+1-555-0205",
     "spec": "Neurology", "license": "MD-MA-67345", "state": "MA", "exp": 10, "dept": "Neurology",
     "fee": 275, "bio": "Neurologist with special interest in migraine, epilepsy, and neurodegenerative diseases."},
]

AVAILABILITY = {
    "monday": ["09:00-12:00", "14:00-17:00"],
    "tuesday": ["09:00-12:00", "14:00-17:00"],
    "wednesday": ["09:00-12:00"],
    "thursday": ["09:00-12:00", "14:00-17:00"],
    "friday": ["09:00-12:00", "14:00-16:00"],
}

CONDITIONS = [
    ("Hypertension", "I10", "chronic"), ("Type 2 Diabetes", "E11.9", "active"),
    ("Asthma", "J45.20", "managed"), ("Migraine", "G43.909", "active"),
    ("Hyperlipidemia", "E78.5", "active"), ("Hypothyroidism", "E03.9", "managed"),
    ("GERD", "K21.0", "managed"), ("Osteoarthritis", "M19.90", "chronic"),
    ("Anxiety Disorder", "F41.1", "active"), ("Allergic Rhinitis", "J30.9", "managed"),
    ("Atrial Fibrillation", "I48.91", "chronic"), ("COPD", "J44.1", "chronic"),
    ("Depression", "F32.9", "active"), ("Iron Deficiency Anemia", "D50.9", "active"),
    ("Chronic Kidney Disease Stage 2", "N18.2", "chronic"),
]

ALLERGIES_POOL = [
    ("Penicillin", "Rash and hives", "severe"), ("Sulfa Drugs", "Breathing difficulty", "severe"),
    ("Aspirin", "Gastrointestinal upset", "moderate"), ("Latex", "Contact dermatitis", "moderate"),
    ("Peanuts", "Anaphylaxis", "life_threatening"), ("Shellfish", "Swelling and hives", "severe"),
    ("Ibuprofen", "Stomach pain", "mild"), ("Codeine", "Nausea and vomiting", "moderate"),
    ("Bee Stings", "Local swelling", "mild"), ("Dust Mites", "Sneezing, runny nose", "mild"),
    ("Pet Dander", "Watery eyes, congestion", "mild"), ("Morphine", "Itching, rash", "moderate"),
]

MEDICATIONS_POOL = [
    ("Lisinopril", "10 mg", "Once daily", "oral", "Blood pressure control"),
    ("Metformin", "500 mg", "Twice daily", "oral", "Blood sugar management"),
    ("Atorvastatin", "20 mg", "Once daily at bedtime", "oral", "Cholesterol control"),
    ("Levothyroxine", "50 mcg", "Once daily on empty stomach", "oral", "Thyroid hormone replacement"),
    ("Amlodipine", "5 mg", "Once daily", "oral", "Blood pressure control"),
    ("Omeprazole", "20 mg", "Once daily before breakfast", "oral", "Acid reflux management"),
    ("Albuterol", "90 mcg", "As needed", "inhalation", "Asthma symptom relief"),
    ("Sertraline", "50 mg", "Once daily", "oral", "Anxiety and depression management"),
    ("Gabapentin", "300 mg", "Three times daily", "oral", "Nerve pain management"),
    ("Losartan", "50 mg", "Once daily", "oral", "Blood pressure and kidney protection"),
    ("Metoprolol", "25 mg", "Twice daily", "oral", "Heart rate and blood pressure control"),
    ("Insulin Glargine", "20 units", "Once daily at bedtime", "subcutaneous", "Long-acting blood sugar control"),
]

REPORT_TYPES = [
    ("Complete Blood Count", "lab"), ("Comprehensive Metabolic Panel", "lab"),
    ("Lipid Panel", "lab"), ("Thyroid Function Test", "lab"),
    ("HbA1c Test", "lab"), ("Chest X-Ray", "imaging"),
    ("Echocardiogram Report", "imaging"), ("Urinalysis", "lab"),
    ("Liver Function Test", "lab"), ("Renal Function Panel", "lab"),
]

LAB_VALUES_POOL = [
    ("Hemoglobin", 14.0, "g/dL", 12.0, 17.5, "718-7"),
    ("White Blood Cell Count", 7.5, "10^3/uL", 4.5, 11.0, "6690-2"),
    ("Platelet Count", 250, "10^3/uL", 150, 400, "777-3"),
    ("Glucose (Fasting)", 95, "mg/dL", 70, 100, "1558-6"),
    ("Creatinine", 1.0, "mg/dL", 0.7, 1.3, "2160-0"),
    ("Total Cholesterol", 195, "mg/dL", 0, 200, "2093-3"),
    ("LDL Cholesterol", 110, "mg/dL", 0, 130, "2089-1"),
    ("HDL Cholesterol", 55, "mg/dL", 40, 60, "2085-9"),
    ("Triglycerides", 130, "mg/dL", 0, 150, "2571-8"),
    ("TSH", 2.5, "mIU/L", 0.4, 4.0, "3016-3"),
    ("HbA1c", 5.7, "%", 4.0, 5.6, "4548-4"),
    ("Sodium", 140, "mEq/L", 136, 145, "2951-2"),
    ("Potassium", 4.2, "mEq/L", 3.5, 5.0, "2823-3"),
    ("ALT", 25, "U/L", 7, 56, "1742-6"),
    ("AST", 22, "U/L", 10, 40, "1920-8"),
    ("BUN", 15, "mg/dL", 7, 20, "3094-0"),
]

PASSWORD = "Demo1234!"


def log(msg):
    print(f"  {msg}")


# ──────────────────────────────────────────────────────────────────────────────
# SEED FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def seed_users():
    """Create 10 patients, 5 doctors, 1 admin."""
    print("\n>>> Seeding users...")
    patient_users = []
    doctor_users = []

    for p in PATIENTS:
        existing = User.query.filter_by(email=p["email"]).first()
        if existing:
            log(f"Patient {p['email']} already exists, skipping.")
            patient_users.append(existing)
            continue
        u = User(email=p["email"], first_name=p["first"], last_name=p["last"],
                 role="patient", phone=p["phone"], is_active=True, is_verified=True)
        u.set_password(PASSWORD)
        db.session.add(u)
        patient_users.append(u)
        log(f"Created patient: {p['email']}")

    for d in DOCTORS:
        existing = User.query.filter_by(email=d["email"]).first()
        if existing:
            log(f"Doctor {d['email']} already exists, skipping.")
            doctor_users.append(existing)
            continue
        u = User(email=d["email"], first_name=d["first"], last_name=d["last"],
                 role="doctor", phone=d["phone"], is_active=True, is_verified=True)
        u.set_password(PASSWORD)
        db.session.add(u)
        doctor_users.append(u)
        log(f"Created doctor: {d['email']}")

    # Admin
    admin_email = "admin@medassist.ai"
    existing_admin = User.query.filter_by(email=admin_email).first()
    if existing_admin:
        log("Admin already exists.")
        admin_user = existing_admin
    else:
        admin_user = User(email=admin_email, first_name="System", last_name="Admin",
                          role="admin", phone="+1-555-0300", is_active=True, is_verified=True)
        admin_user.set_password(PASSWORD)
        db.session.add(admin_user)
        log("Created admin: admin@medassist.ai")

    db.session.flush()
    return patient_users, doctor_users, admin_user


def seed_patient_profiles(patient_users, doctor_users):
    """Create patient profiles with medical data."""
    print("\n>>> Seeding patient profiles...")
    profiles = []
    for i, u in enumerate(patient_users):
        existing = PatientProfile.query.filter_by(user_id=u.id).first()
        if existing:
            profiles.append(existing)
            continue
        p_data = PATIENTS[i]
        doc = doctor_users[i % len(doctor_users)]
        profile = PatientProfile(
            user_id=u.id,
            date_of_birth=p_data["dob"],
            gender=p_data["gender"],
            blood_type=p_data["blood"],
            height_cm=Decimal(str(p_data["height"])),
            weight_kg=Decimal(str(p_data["weight"])),
            emergency_contact=p_data["emergency"],
            insurance_info=p_data["insurance"],
            assigned_doctor_id=doc.id,
        )
        db.session.add(profile)
        profiles.append(profile)
        log(f"Created profile for {u.first_name} {u.last_name} → assigned to {doc.first_name}")
    db.session.flush()
    return profiles


def seed_doctor_profiles(doctor_users):
    """Create doctor profiles with specializations."""
    print("\n>>> Seeding doctor profiles...")
    profiles = []
    for i, u in enumerate(doctor_users):
        existing = DoctorProfile.query.filter_by(user_id=u.id).first()
        if existing:
            profiles.append(existing)
            continue
        d_data = DOCTORS[i]
        profile = DoctorProfile(
            user_id=u.id,
            specialization=d_data["spec"],
            license_number=d_data["license"],
            license_state=d_data["state"],
            years_of_experience=d_data["exp"],
            department=d_data["dept"],
            consultation_fee=Decimal(str(d_data["fee"])),
            bio=d_data["bio"],
            availability=AVAILABILITY,
        )
        db.session.add(profile)
        profiles.append(profile)
        log(f"Created doctor profile: {d_data['spec']}")
    db.session.flush()
    return profiles


def seed_medical_history(patient_users, patient_profiles, doctor_users):
    """Add 2-4 conditions per patient."""
    print("\n>>> Seeding medical history...")
    count = 0
    for i, u in enumerate(patient_users):
        profile = patient_profiles[i]
        existing = MedicalHistory.query.filter_by(patient_id=profile.id).count()
        if existing > 0:
            continue
        num_conditions = random.randint(2, 4)
        selected = random.sample(CONDITIONS, num_conditions)
        for cond_name, icd, status in selected:
            mh = MedicalHistory(
                patient_id=profile.id,
                condition_name=cond_name,
                diagnosis_date=date(random.randint(2018, 2025), random.randint(1, 12), random.randint(1, 28)),
                status=status,
                icd_10_code=icd,
                notes=f"Patient diagnosed with {cond_name}. Currently {status}.",
                diagnosed_by=doctor_users[i % len(doctor_users)].id,
                created_by=doctor_users[i % len(doctor_users)].id,
            )
            db.session.add(mh)
            count += 1
    db.session.flush()
    log(f"Created {count} medical history records.")


def seed_allergies(patient_users, patient_profiles, doctor_users):
    """Add 1-3 allergies per patient."""
    print("\n>>> Seeding allergies...")
    count = 0
    for i, u in enumerate(patient_users):
        profile = patient_profiles[i]
        existing = Allergy.query.filter_by(patient_id=profile.id).count()
        if existing > 0:
            continue
        num = random.randint(1, 3)
        selected = random.sample(ALLERGIES_POOL, num)
        for allergen, reaction, severity in selected:
            a = Allergy(
                patient_id=profile.id,
                allergen=allergen,
                reaction=reaction,
                severity=severity,
                diagnosed_date=date(random.randint(2015, 2024), random.randint(1, 12), 1),
                created_by=doctor_users[i % len(doctor_users)].id,
            )
            db.session.add(a)
            count += 1
    db.session.flush()
    log(f"Created {count} allergy records.")


def seed_vitals(patient_users):
    """Add 20 vitals readings per patient over last 30 days."""
    print("\n>>> Seeding vitals readings...")
    count = 0
    for u in patient_users:
        existing = VitalsReading.query.filter_by(patient_id=u.id).count()
        if existing >= 10:
            continue
        for day_offset in range(20):
            ts = now - timedelta(days=day_offset, hours=random.randint(6, 22))
            is_anomalous = random.random() < 0.1
            hr = random.randint(55, 100) if not is_anomalous else random.randint(110, 140)
            sys_bp = random.randint(110, 135) if not is_anomalous else random.randint(145, 180)
            dia_bp = random.randint(65, 85) if not is_anomalous else random.randint(90, 110)
            temp = round(random.uniform(97.0, 99.0), 1) if not is_anomalous else round(random.uniform(100.5, 103.0), 1)
            o2 = round(random.uniform(96, 100), 1) if not is_anomalous else round(random.uniform(88, 94), 1)
            rr = random.randint(12, 20) if not is_anomalous else random.randint(22, 30)
            glucose = round(random.uniform(75, 110), 1) if not is_anomalous else round(random.uniform(180, 300), 1)

            v = VitalsReading(
                patient_id=u.id,
                heart_rate=hr,
                blood_pressure_systolic=sys_bp,
                blood_pressure_diastolic=dia_bp,
                temperature=Decimal(str(temp)),
                oxygen_saturation=Decimal(str(o2)),
                respiratory_rate=rr,
                blood_glucose=Decimal(str(glucose)),
                pain_level=random.randint(0, 3) if not is_anomalous else random.randint(5, 8),
                is_manual_entry=random.choice([True, False]),
                is_anomalous=is_anomalous,
                notes="Routine check" if not is_anomalous else "Abnormal reading flagged",
                recorded_at=ts,
                created_by=u.id,
            )
            db.session.add(v)
            count += 1
    db.session.flush()
    log(f"Created {count} vitals readings.")


def seed_appointments(patient_users, doctor_users):
    """Create past and upcoming appointments."""
    print("\n>>> Seeding appointments...")
    count = 0
    appt_list = []
    types = ["in_person", "telemedicine", "follow_up"]
    reasons = [
        "Routine checkup", "Follow-up on blood work", "Medication review",
        "Chest pain evaluation", "Blood pressure monitoring", "Diabetes management",
        "Headache consultation", "Annual physical", "Vaccination appointment",
        "Lab results discussion", "Pre-surgical consultation", "Weight management"
    ]

    for i, patient in enumerate(patient_users):
        doc = doctor_users[i % len(doctor_users)]
        # 2 past completed appointments
        for j in range(2):
            past_date = now - timedelta(days=random.randint(7, 60))
            a = Appointment(
                patient_id=patient.id, doctor_id=doc.id,
                appointment_type=random.choice(types),
                status="completed",
                scheduled_at=past_date,
                duration_minutes=random.choice([15, 30, 45]),
                reason=random.choice(reasons),
                notes=f"Completed visit. Patient in stable condition.",
                created_by=patient.id,
            )
            db.session.add(a)
            appt_list.append(a)
            count += 1

        # 1 upcoming confirmed appointment
        future_date = now + timedelta(days=random.randint(1, 14), hours=random.randint(9, 16))
        a = Appointment(
            patient_id=patient.id, doctor_id=doc.id,
            appointment_type=random.choice(types),
            status="confirmed",
            scheduled_at=future_date,
            duration_minutes=30,
            reason=random.choice(reasons),
            created_by=patient.id,
        )
        db.session.add(a)
        appt_list.append(a)
        count += 1

        # 1 upcoming scheduled appointment
        future_date2 = now + timedelta(days=random.randint(15, 30), hours=random.randint(9, 16))
        a = Appointment(
            patient_id=patient.id, doctor_id=doctor_users[(i + 1) % len(doctor_users)].id,
            appointment_type="follow_up",
            status="scheduled",
            scheduled_at=future_date2,
            duration_minutes=30,
            reason="Follow-up visit",
            created_by=patient.id,
        )
        db.session.add(a)
        appt_list.append(a)
        count += 1

    db.session.flush()
    log(f"Created {count} appointments.")
    return appt_list


def seed_medications(patient_users, doctor_users):
    """Prescribe 2-3 medications per patient."""
    print("\n>>> Seeding medications...")
    count = 0
    for i, patient in enumerate(patient_users):
        existing = Medication.query.filter_by(patient_id=patient.id).count()
        if existing > 0:
            continue
        doc = doctor_users[i % len(doctor_users)]
        num = random.randint(2, 3)
        selected = random.sample(MEDICATIONS_POOL, num)
        for name, dosage, freq, route, reason in selected:
            m = Medication(
                patient_id=patient.id,
                name=name,
                dosage=dosage,
                frequency=freq,
                route=route,
                prescribed_by=doc.id,
                start_date=date.today() - timedelta(days=random.randint(30, 365)),
                end_date=date.today() + timedelta(days=random.randint(30, 180)) if random.random() > 0.3 else None,
                status=random.choice(["active", "active", "active", "completed"]),
                reason=reason,
                side_effects="Monitor for common side effects.",
                refills_remaining=random.randint(0, 5),
                created_by=doc.id,
            )
            db.session.add(m)
            count += 1
    db.session.flush()
    log(f"Created {count} medications.")


def seed_care_plans(patient_users, doctor_users):
    """Create a care plan with goals and activities per patient."""
    print("\n>>> Seeding care plans...")
    count = 0
    plan_titles = [
        "Hypertension Management Plan", "Diabetes Control Program",
        "Weight Management Plan", "Cardiovascular Health Plan",
        "Respiratory Health Plan", "Mental Wellness Plan",
        "Chronic Pain Management", "Post-Surgery Recovery Plan",
        "Thyroid Management Plan", "Preventive Health Plan",
    ]
    for i, patient in enumerate(patient_users):
        existing = CarePlan.query.filter_by(patient_id=patient.id).count()
        if existing > 0:
            continue
        doc = doctor_users[i % len(doctor_users)]
        plan = CarePlan(
            patient_id=patient.id, doctor_id=doc.id,
            title=plan_titles[i],
            description=f"Comprehensive care plan for {patient.first_name} focusing on {plan_titles[i].lower()}.",
            status="active",
            start_date=date.today() - timedelta(days=random.randint(7, 30)),
            end_date=date.today() + timedelta(days=90),
            ai_recommendations={
                "lifestyle": ["Regular exercise 30 min/day", "Balanced diet", "Adequate sleep 7-8 hours"],
                "monitoring": ["Weekly blood pressure checks", "Monthly lab work"],
            },
            created_by=doc.id,
        )
        db.session.add(plan)
        db.session.flush()

        # 2 goals per plan
        goals = []
        goal_data = [
            ("Blood Pressure Control", "Maintain BP below 130/80", "130/80", "mmHg", "135/82"),
            ("Weight Target", "Reach healthy BMI range", "72", "kg", "76"),
            ("Blood Sugar Control", "Maintain HbA1c below 6.5%", "6.5", "%", "6.8"),
            ("Exercise Goal", "Walk 10,000 steps daily", "10000", "steps/day", "7500"),
        ]
        for title, desc, target, unit, current in random.sample(goal_data, 2):
            g = CarePlanGoal(
                care_plan_id=plan.id, title=title, description=desc,
                target_value=target, current_value=current,
                unit=unit, status=random.choice(["in_progress", "in_progress", "achieved"]),
                target_date=date.today() + timedelta(days=60),
            )
            db.session.add(g)
            goals.append(g)
        db.session.flush()

        # 3 activities per plan
        activities_data = [
            ("Take prescribed medication", "medication", "Daily"),
            ("30-minute brisk walk", "exercise", "Daily"),
            ("Follow low-sodium diet", "diet", "Daily"),
            ("Check blood pressure", "monitoring", "Twice daily"),
            ("Attend follow-up appointment", "appointment", "Monthly"),
            ("Practice deep breathing exercises", "exercise", "Twice daily"),
        ]
        for title, atype, freq in random.sample(activities_data, 3):
            act = CarePlanActivity(
                care_plan_id=plan.id,
                goal_id=goals[0].id if random.random() > 0.5 else None,
                title=title, activity_type=atype, frequency=freq,
                status=random.choice(["pending", "in_progress", "completed"]),
            )
            db.session.add(act)
        count += 1

    db.session.flush()
    log(f"Created {count} care plans with goals and activities.")


def seed_reports(patient_users, doctor_users):
    """Create medical reports with lab values."""
    print("\n>>> Seeding medical reports...")
    count = 0
    for i, patient in enumerate(patient_users):
        existing = MedicalReport.query.filter_by(patient_id=patient.id).count()
        if existing > 0:
            continue
        doc = doctor_users[i % len(doctor_users)]
        # 2 reports per patient
        for report_title, report_type in random.sample(REPORT_TYPES, 2):
            report = MedicalReport(
                patient_id=patient.id,
                report_type=report_type,
                title=f"{report_title} - {patient.first_name} {patient.last_name}",
                content=f"Report for {patient.first_name}. All results within expected parameters with minor variations noted.",
                ai_summary=f"AI Analysis: {report_title} shows generally normal results. A few values warrant monitoring.",
                ai_analysis={"confidence": round(random.uniform(0.85, 0.98), 2), "findings": ["Normal range results", "Continued monitoring recommended"]},
                status="reviewed",
                reviewed_by=doc.id,
                reviewed_at=now - timedelta(days=random.randint(1, 14)),
                created_by=doc.id,
            )
            db.session.add(report)
            db.session.flush()

            # Add 4-6 lab values per report
            if report_type == "lab":
                for test_name, base_val, unit, ref_min, ref_max, loinc in random.sample(LAB_VALUES_POOL, random.randint(4, 6)):
                    variation = random.uniform(0.85, 1.15)
                    value = round(base_val * variation, 2)
                    is_abnormal = value < ref_min or value > ref_max
                    lv = LabValue(
                        report_id=report.id, patient_id=patient.id,
                        test_name=test_name, value=Decimal(str(value)),
                        unit=unit, reference_min=Decimal(str(ref_min)), reference_max=Decimal(str(ref_max)),
                        is_abnormal=is_abnormal, loinc_code=loinc,
                        collected_at=now - timedelta(days=random.randint(1, 14)),
                    )
                    db.session.add(lv)
            count += 1
    db.session.flush()
    log(f"Created {count} medical reports with lab values.")


def seed_notifications(patient_users, doctor_users):
    """Create notifications for all users."""
    print("\n>>> Seeding notifications...")
    count = 0
    notif_templates = [
        ("appointment_reminder", "Upcoming Appointment", "You have an appointment scheduled for tomorrow at 10:00 AM."),
        ("medication_reminder", "Medication Reminder", "Time to take your prescribed medication: Lisinopril 10mg."),
        ("vitals_alert", "Vitals Alert", "Your recent blood pressure reading was slightly elevated. Please monitor."),
        ("lab_results", "Lab Results Ready", "Your recent lab results are now available for review."),
        ("care_plan_update", "Care Plan Updated", "Your doctor has updated your care plan. Please review the changes."),
        ("system_message", "Welcome to MedAssist AI", "Welcome! Complete your profile to get personalized health insights."),
    ]

    for user in patient_users + doctor_users:
        for ntype, title, message in random.sample(notif_templates, random.randint(2, 4)):
            is_read = random.random() > 0.4
            n = Notification(
                user_id=user.id, type=ntype, title=title, message=message,
                read=is_read, channel="in_app",
                read_at=now - timedelta(hours=random.randint(1, 48)) if is_read else None,
                sent_at=now - timedelta(hours=random.randint(1, 72)),
            )
            db.session.add(n)
            count += 1
    db.session.flush()
    log(f"Created {count} notifications.")


def seed_conversations(patient_users):
    """Create AI chat conversations."""
    print("\n>>> Seeding conversations...")
    count = 0
    conversation_data = [
        ("symptom_analyst", "Headache and Fatigue Discussion", [
            {"role": "user", "content": "I've been having persistent headaches and fatigue for the past week."},
            {"role": "assistant", "content": "I'm sorry to hear that. Let me help analyze your symptoms. Can you describe the headache - is it throbbing, sharp, or dull? Where exactly is the pain located?"},
            {"role": "user", "content": "It's a dull ache mostly in the front of my head, and it gets worse in the afternoon."},
            {"role": "assistant", "content": "A frontal dull headache that worsens in the afternoon could be tension-type headache. Combined with fatigue, this could indicate dehydration, sleep issues, or stress. I recommend tracking your water intake and sleep patterns. If symptoms persist beyond 2 weeks, please schedule a visit with your doctor."},
        ]),
        ("general", "Diet and Nutrition Advice", [
            {"role": "user", "content": "What diet changes can help manage my blood pressure?"},
            {"role": "assistant", "content": "Great question! The DASH diet is highly recommended. Key changes: reduce sodium to less than 2,300mg/day, increase potassium-rich foods (bananas, sweet potatoes), eat more whole grains, fruits, and vegetables, limit red meat and saturated fats, and reduce alcohol intake. Would you like a detailed meal plan?"},
        ]),
        ("drug_interaction", "Medication Interaction Check", [
            {"role": "user", "content": "Can I take ibuprofen while on lisinopril?"},
            {"role": "assistant", "content": "Caution is advised. NSAIDs like ibuprofen can reduce the effectiveness of ACE inhibitors like lisinopril and may increase the risk of kidney problems. For pain relief, acetaminophen (Tylenol) is generally a safer alternative. Always consult your prescribing doctor before combining medications."},
        ]),
    ]

    for patient in patient_users:
        for agent_type, title, messages in random.sample(conversation_data, random.randint(1, 2)):
            timestamped_msgs = []
            for j, msg in enumerate(messages):
                timestamped_msgs.append({
                    **msg,
                    "timestamp": (now - timedelta(hours=random.randint(1, 48), minutes=j * 2)).isoformat(),
                })
            c = Conversation(
                patient_id=patient.id,
                agent_type=agent_type,
                title=title,
                messages=timestamped_msgs,
                status="closed" if random.random() > 0.3 else "active",
            )
            db.session.add(c)
            count += 1
    db.session.flush()
    log(f"Created {count} conversations.")


def seed_symptom_sessions(patient_users, doctor_users):
    """Create completed symptom analysis sessions."""
    print("\n>>> Seeding symptom sessions...")
    count = 0
    sessions_data = [
        ("Persistent headache and dizziness for 3 days",
         [{"name": "Headache", "severity": 6, "duration_days": 3}, {"name": "Dizziness", "severity": 4, "duration_days": 3}],
         {"differential_diagnoses": [{"condition": "Tension Headache", "confidence": 0.7}, {"condition": "Migraine", "confidence": 0.2}, {"condition": "Dehydration", "confidence": 0.1}], "urgency_score": 3},
         "semi_urgent", "Schedule appointment with primary care. Monitor for worsening symptoms."),
        ("Chest tightness and shortness of breath",
         [{"name": "Chest Tightness", "severity": 7, "duration_days": 1}, {"name": "Shortness of Breath", "severity": 5, "duration_days": 1}],
         {"differential_diagnoses": [{"condition": "Anxiety", "confidence": 0.4}, {"condition": "Asthma Exacerbation", "confidence": 0.35}, {"condition": "Cardiac", "confidence": 0.25}], "urgency_score": 7},
         "urgent", "Immediate medical evaluation recommended. If symptoms worsen, call 911."),
        ("Joint pain and morning stiffness",
         [{"name": "Joint Pain", "severity": 5, "duration_days": 14}, {"name": "Morning Stiffness", "severity": 4, "duration_days": 14}],
         {"differential_diagnoses": [{"condition": "Osteoarthritis", "confidence": 0.6}, {"condition": "Rheumatoid Arthritis", "confidence": 0.25}, {"condition": "Fibromyalgia", "confidence": 0.15}], "urgency_score": 4},
         "semi_urgent", "Schedule rheumatology consultation. OTC anti-inflammatory for symptom relief."),
        ("Fatigue and weight gain over 2 months",
         [{"name": "Fatigue", "severity": 6, "duration_days": 60}, {"name": "Weight Gain", "severity": 3, "duration_days": 60}],
         {"differential_diagnoses": [{"condition": "Hypothyroidism", "confidence": 0.5}, {"condition": "Depression", "confidence": 0.3}, {"condition": "Sleep Apnea", "confidence": 0.2}], "urgency_score": 3},
         "non_urgent", "Recommend thyroid function tests. Follow up in 1-2 weeks."),
    ]

    for i, patient in enumerate(patient_users):
        existing = SymptomSession.query.filter_by(patient_id=patient.id).count()
        if existing > 0:
            continue
        complaint, symptoms, analysis, triage, action = sessions_data[i % len(sessions_data)]
        doc = doctor_users[i % len(doctor_users)]
        s = SymptomSession(
            patient_id=patient.id,
            status="completed",
            chief_complaint=complaint,
            symptoms=symptoms,
            ai_analysis=analysis,
            triage_level=triage,
            recommended_action=action,
            escalated_to=doc.id if triage in ["urgent", "emergency"] else None,
            conversation_log=[
                {"role": "user", "content": complaint, "timestamp": (now - timedelta(hours=random.randint(24, 72))).isoformat()},
                {"role": "assistant", "content": f"I've analyzed your symptoms. Based on my assessment, this is {triage}. {action}", "timestamp": (now - timedelta(hours=random.randint(23, 71))).isoformat()},
            ],
            completed_at=now - timedelta(hours=random.randint(1, 48)),
        )
        db.session.add(s)
        count += 1
    db.session.flush()
    log(f"Created {count} symptom sessions.")


def seed_alerts(patient_users, doctor_users):
    """Create monitoring alerts for anomalous readings."""
    print("\n>>> Seeding monitoring alerts...")
    count = 0
    alert_types = [
        ("heart_rate_high", "high", "Elevated Heart Rate", "Heart rate reading above normal threshold (>100 bpm)."),
        ("bp_high", "critical", "High Blood Pressure Alert", "Blood pressure reading significantly above normal (>140/90 mmHg)."),
        ("spo2_low", "critical", "Low Oxygen Saturation", "SpO2 dropped below 92%. Immediate attention recommended."),
        ("temperature_high", "medium", "Elevated Temperature", "Body temperature above 100.4°F. Monitor for fever."),
        ("glucose_high", "high", "High Blood Glucose", "Blood glucose reading above 180 mg/dL. Adjust medication if needed."),
    ]

    for i, patient in enumerate(patient_users[:6]):  # alerts for first 6 patients
        existing = MonitoringAlert.query.filter_by(patient_id=patient.id).count()
        if existing > 0:
            continue
        doc = doctor_users[i % len(doctor_users)]
        atype, severity, title, desc = alert_types[i % len(alert_types)]
        statuses = ["active", "acknowledged", "resolved"]
        status = statuses[i % 3]
        a = MonitoringAlert(
            patient_id=patient.id,
            alert_type=atype, severity=severity, title=title, description=desc,
            ai_analysis={"recommendation": "Review patient vitals history and adjust treatment plan.", "confidence": 0.87},
            status=status,
            acknowledged_by=doc.id if status in ["acknowledged", "resolved"] else None,
            acknowledged_at=now - timedelta(hours=2) if status in ["acknowledged", "resolved"] else None,
            resolved_by=doc.id if status == "resolved" else None,
            resolved_at=now - timedelta(hours=1) if status == "resolved" else None,
            escalation_level=1 if severity in ["high", "critical"] else 0,
        )
        db.session.add(a)
        count += 1
    db.session.flush()
    log(f"Created {count} monitoring alerts.")


def seed_audit_logs(patient_users, doctor_users, admin_user):
    """Create HIPAA audit log entries."""
    print("\n>>> Seeding audit logs...")
    count = 0
    actions = [
        ("read", "patient_profile", "GET", "/api/v1/patients/"),
        ("read", "vitals", "GET", "/api/v1/vitals/"),
        ("write", "vitals", "POST", "/api/v1/vitals/"),
        ("read", "medical_report", "GET", "/api/v1/reports/"),
        ("read", "medication", "GET", "/api/v1/medications/"),
        ("write", "appointment", "POST", "/api/v1/appointments"),
        ("read", "care_plan", "GET", "/api/v1/care-plans"),
        ("export", "medical_report", "GET", "/api/v1/reports/download"),
    ]

    all_users = doctor_users + [admin_user]
    for user in all_users:
        for action, resource, method, path in random.sample(actions, random.randint(3, 5)):
            patient = random.choice(patient_users)
            al = AuditLog(
                user_id=user.id,
                action=action,
                resource_type=resource,
                resource_id=patient.id,
                patient_id=patient.id,
                ip_address=f"10.128.0.{random.randint(2, 254)}",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                request_method=method,
                request_path=path,
                status_code=200,
                details={"accessed_fields": ["name", "vitals", "medications"]},
            )
            db.session.add(al)
            count += 1
    db.session.flush()
    log(f"Created {count} audit log entries.")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    app = create_app("production")
    with app.app_context():
        print("=" * 60)
        print("  MedAssist AI — Production Data Seed")
        print("=" * 60)

        # Create tables if they don't exist
        db.create_all()

        try:
            patient_users, doctor_users, admin_user = seed_users()
            db.session.commit()

            patient_profiles = seed_patient_profiles(patient_users, doctor_users)
            doctor_profiles = seed_doctor_profiles(doctor_users)
            db.session.commit()

            seed_medical_history(patient_users, patient_profiles, doctor_users)
            seed_allergies(patient_users, patient_profiles, doctor_users)
            db.session.commit()

            seed_vitals(patient_users)
            db.session.commit()

            seed_appointments(patient_users, doctor_users)
            db.session.commit()

            seed_medications(patient_users, doctor_users)
            db.session.commit()

            seed_care_plans(patient_users, doctor_users)
            db.session.commit()

            seed_reports(patient_users, doctor_users)
            db.session.commit()

            seed_notifications(patient_users, doctor_users)
            db.session.commit()

            seed_conversations(patient_users)
            db.session.commit()

            seed_symptom_sessions(patient_users, doctor_users)
            db.session.commit()

            seed_alerts(patient_users, doctor_users)
            db.session.commit()

            seed_audit_logs(patient_users, doctor_users, admin_user)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # Print summary
        print("\n" + "=" * 60)
        print("  SEED COMPLETE — Summary")
        print("=" * 60)
        tables = [
            ("Users", User), ("Patient Profiles", PatientProfile),
            ("Doctor Profiles", DoctorProfile), ("Medical History", MedicalHistory),
            ("Allergies", Allergy), ("Vitals Readings", VitalsReading),
            ("Appointments", Appointment), ("Medications", Medication),
            ("Care Plans", CarePlan), ("Care Plan Goals", CarePlanGoal),
            ("Care Plan Activities", CarePlanActivity), ("Medical Reports", MedicalReport),
            ("Lab Values", LabValue), ("Notifications", Notification),
            ("Conversations", Conversation), ("Symptom Sessions", SymptomSession),
            ("Monitoring Alerts", MonitoringAlert), ("Audit Logs", AuditLog),
        ]
        for name, model in tables:
            print(f"  {name:25s} {model.query.count():>6d} records")

        print(f"\n  Password for all accounts: {PASSWORD}")
        print("=" * 60)


if __name__ == "__main__":
    main()
