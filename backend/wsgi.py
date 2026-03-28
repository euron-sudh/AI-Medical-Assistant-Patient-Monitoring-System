"""WSGI entry point for MedAssist AI backend."""

import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app import create_app
from app.extensions import db

app = create_app()


def _seed_all_demo_data() -> None:
    """Seed the database with comprehensive demo data.

    Creates doctors, admin, patients with full medical profiles,
    vitals, appointments, reports, care plans, alerts, and notifications.
    """
    from app.models.user import User
    from app.models.patient import PatientProfile, MedicalHistory, Allergy
    from app.models.doctor import DoctorProfile
    from app.models.vitals import VitalsReading
    from app.models.medication import Medication
    from app.models.appointment import Appointment
    from app.models.report import MedicalReport, LabValue
    from app.models.care_plan import CarePlan, CarePlanGoal, CarePlanActivity
    from app.models.alert import MonitoringAlert
    from app.models.notification import Notification

    now = datetime.now(timezone.utc)
    today = date.today()
    password = "Demo1234!"

    # ------------------------------------------------------------------ #
    # 1. Doctors (3) — keep doctor@demo.dev for backward compat
    # ------------------------------------------------------------------ #
    doctors_data = [
        {
            "email": "doctor@demo.dev",
            "first_name": "Sarah",
            "last_name": "Chen",
            "phone": "+1-555-201-0001",
            "specialization": "Internal Medicine",
            "license_number": "MD-2019-04821",
            "license_state": "CA",
            "years_of_experience": 12,
            "department": "General Medicine",
            "consultation_fee": Decimal("175.00"),
            "bio": "Board-certified internist with expertise in chronic disease management and preventive care.",
        },
        {
            "email": "doctor.cardio@demo.dev",
            "first_name": "James",
            "last_name": "Okonkwo",
            "phone": "+1-555-201-0002",
            "specialization": "Cardiology",
            "license_number": "MD-2015-03194",
            "license_state": "CA",
            "years_of_experience": 18,
            "department": "Cardiology",
            "consultation_fee": Decimal("250.00"),
            "bio": "Fellowship-trained cardiologist specializing in heart failure and electrophysiology.",
        },
        {
            "email": "doctor.neuro@demo.dev",
            "first_name": "Maria",
            "last_name": "Rodriguez",
            "phone": "+1-555-201-0003",
            "specialization": "Neurology",
            "license_number": "MD-2017-05673",
            "license_state": "CA",
            "years_of_experience": 14,
            "department": "Neurology",
            "consultation_fee": Decimal("225.00"),
            "bio": "Neurologist with a focus on headache medicine, epilepsy, and neurodegenerative disorders.",
        },
    ]

    doctor_users: list[User] = []
    for dd in doctors_data:
        u = User(
            email=dd["email"],
            first_name=dd["first_name"],
            last_name=dd["last_name"],
            role="doctor",
            phone=dd["phone"],
            is_active=True,
            is_verified=True,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.flush()

        dp = DoctorProfile(
            user_id=u.id,
            specialization=dd["specialization"],
            license_number=dd["license_number"],
            license_state=dd["license_state"],
            years_of_experience=dd["years_of_experience"],
            department=dd["department"],
            consultation_fee=dd["consultation_fee"],
            bio=dd["bio"],
            availability={
                "monday": ["09:00-12:00", "14:00-17:00"],
                "tuesday": ["09:00-12:00", "14:00-17:00"],
                "wednesday": ["09:00-12:00"],
                "thursday": ["09:00-12:00", "14:00-17:00"],
                "friday": ["09:00-12:00", "14:00-16:00"],
            },
        )
        db.session.add(dp)
        doctor_users.append(u)

    # ------------------------------------------------------------------ #
    # 2. Admin (1) — keep admin@demo.dev for backward compat
    # ------------------------------------------------------------------ #
    admin_user = User(
        email="admin@demo.dev",
        first_name="Robert",
        last_name="Martinez",
        role="admin",
        phone="+1-555-201-0099",
        is_active=True,
        is_verified=True,
    )
    admin_user.set_password(password)
    db.session.add(admin_user)

    db.session.flush()

    # ------------------------------------------------------------------ #
    # 3. Patients (10) — keep patient@demo.dev for backward compat
    # ------------------------------------------------------------------ #
    patients_raw = [
        {
            "email": "patient@demo.dev",
            "first_name": "Emily",
            "last_name": "Johnson",
            "phone": "+1-555-301-0001",
            "dob": date(1988, 3, 14),
            "gender": "Female",
            "blood_type": "O+",
            "height_cm": Decimal("165.0"),
            "weight_kg": Decimal("62.5"),
            "emergency_contact": {"name": "Michael Johnson", "phone": "+1-555-301-9001", "relationship": "Spouse"},
            "insurance_info": {"provider": "Blue Cross Blue Shield", "policy_number": "BCBS-9928374", "group_number": "GRP-4421"},
            "conditions": [
                ("Type 2 Diabetes Mellitus", "E11.9", "chronic", "Diagnosed during routine screening. Managed with metformin and lifestyle changes."),
                ("Essential Hypertension", "I10", "managed", "Blood pressure controlled with lisinopril."),
                ("Seasonal Allergic Rhinitis", "J30.2", "active", "Worsens in spring. Uses cetirizine PRN."),
            ],
            "allergies": [
                ("Penicillin", "Anaphylaxis — hives, throat swelling", "severe"),
                ("Sulfa drugs", "Skin rash", "moderate"),
            ],
            "medications": [
                ("Metformin", "500 mg", "Twice daily", "oral", "Type 2 Diabetes management"),
                ("Lisinopril", "10 mg", "Once daily", "oral", "Hypertension management"),
                ("Cetirizine", "10 mg", "Once daily PRN", "oral", "Seasonal allergies"),
                ("Vitamin D3", "2000 IU", "Once daily", "oral", "Vitamin D deficiency prevention"),
            ],
        },
        {
            "email": "patient.williams@demo.dev",
            "first_name": "Marcus",
            "last_name": "Williams",
            "phone": "+1-555-301-0002",
            "dob": date(1975, 7, 22),
            "gender": "Male",
            "blood_type": "A+",
            "height_cm": Decimal("180.0"),
            "weight_kg": Decimal("95.3"),
            "emergency_contact": {"name": "Linda Williams", "phone": "+1-555-301-9002", "relationship": "Wife"},
            "insurance_info": {"provider": "Aetna", "policy_number": "AET-5567281", "group_number": "GRP-8812"},
            "conditions": [
                ("Coronary Artery Disease", "I25.10", "chronic", "Three-vessel disease. Status post CABG 2022."),
                ("Hyperlipidemia", "E78.5", "managed", "LDL controlled with atorvastatin."),
                ("Obesity", "E66.01", "active", "BMI 29.4. Dietary counseling in progress."),
                ("Obstructive Sleep Apnea", "G47.33", "managed", "Uses CPAP nightly."),
            ],
            "allergies": [
                ("Aspirin", "GI bleeding", "severe"),
                ("Iodinated contrast", "Urticaria", "moderate"),
                ("Shellfish", "Hives and nausea", "moderate"),
            ],
            "medications": [
                ("Atorvastatin", "40 mg", "Once daily at bedtime", "oral", "Hyperlipidemia"),
                ("Clopidogrel", "75 mg", "Once daily", "oral", "Post-CABG antiplatelet therapy"),
                ("Metoprolol Succinate", "50 mg", "Once daily", "oral", "Heart rate control"),
                ("Lisinopril", "20 mg", "Once daily", "oral", "Blood pressure and cardiac remodeling"),
                ("Pantoprazole", "40 mg", "Once daily", "oral", "GI protection"),
            ],
        },
        {
            "email": "patient.patel@demo.dev",
            "first_name": "Priya",
            "last_name": "Patel",
            "phone": "+1-555-301-0003",
            "dob": date(1992, 11, 5),
            "gender": "Female",
            "blood_type": "B+",
            "height_cm": Decimal("158.0"),
            "weight_kg": Decimal("54.0"),
            "emergency_contact": {"name": "Rajesh Patel", "phone": "+1-555-301-9003", "relationship": "Father"},
            "insurance_info": {"provider": "UnitedHealthcare", "policy_number": "UHC-3347192", "group_number": "GRP-6623"},
            "conditions": [
                ("Generalized Anxiety Disorder", "F41.1", "managed", "Managed with sertraline and CBT therapy."),
                ("Iron Deficiency Anemia", "D50.9", "active", "Supplementing with ferrous sulfate."),
                ("Migraine without Aura", "G43.009", "chronic", "Frequent episodes, 3-4 per month."),
            ],
            "allergies": [
                ("Latex", "Contact dermatitis", "moderate"),
                ("Codeine", "Severe nausea and vomiting", "moderate"),
            ],
            "medications": [
                ("Sertraline", "100 mg", "Once daily", "oral", "Anxiety management"),
                ("Ferrous Sulfate", "325 mg", "Once daily", "oral", "Iron deficiency anemia"),
                ("Sumatriptan", "50 mg", "PRN for migraine", "oral", "Acute migraine relief"),
                ("Magnesium Oxide", "400 mg", "Once daily", "oral", "Migraine prophylaxis"),
            ],
        },
        {
            "email": "patient.thompson@demo.dev",
            "first_name": "David",
            "last_name": "Thompson",
            "phone": "+1-555-301-0004",
            "dob": date(1965, 1, 30),
            "gender": "Male",
            "blood_type": "AB+",
            "height_cm": Decimal("175.0"),
            "weight_kg": Decimal("88.0"),
            "emergency_contact": {"name": "Karen Thompson", "phone": "+1-555-301-9004", "relationship": "Wife"},
            "insurance_info": {"provider": "Cigna", "policy_number": "CIG-7782945", "group_number": "GRP-1109"},
            "conditions": [
                ("Chronic Obstructive Pulmonary Disease", "J44.1", "chronic", "Former smoker (30 pack-years). On tiotropium and albuterol."),
                ("Type 2 Diabetes Mellitus", "E11.65", "managed", "Controlled with insulin glargine and metformin."),
                ("Peripheral Neuropathy", "G62.9", "active", "Secondary to diabetes. Gabapentin for pain."),
                ("Benign Prostatic Hyperplasia", "N40.0", "managed", "Tamsulosin provides symptom relief."),
            ],
            "allergies": [
                ("ACE Inhibitors", "Angioedema", "severe"),
                ("Erythromycin", "Gastrointestinal distress", "mild"),
            ],
            "medications": [
                ("Tiotropium", "18 mcg", "Once daily inhaled", "inhalation", "COPD maintenance"),
                ("Albuterol", "90 mcg", "PRN 2 puffs", "inhalation", "COPD rescue inhaler"),
                ("Insulin Glargine", "24 units", "Once daily at bedtime", "subcutaneous", "Basal insulin for diabetes"),
                ("Metformin", "1000 mg", "Twice daily", "oral", "Type 2 Diabetes management"),
                ("Gabapentin", "300 mg", "Three times daily", "oral", "Neuropathic pain"),
            ],
        },
        {
            "email": "patient.kim@demo.dev",
            "first_name": "Soo-Jin",
            "last_name": "Kim",
            "phone": "+1-555-301-0005",
            "dob": date(1998, 5, 18),
            "gender": "Female",
            "blood_type": "A-",
            "height_cm": Decimal("162.0"),
            "weight_kg": Decimal("55.0"),
            "emergency_contact": {"name": "Hyun Kim", "phone": "+1-555-301-9005", "relationship": "Mother"},
            "insurance_info": {"provider": "Kaiser Permanente", "policy_number": "KP-1129384", "group_number": "GRP-5501"},
            "conditions": [
                ("Asthma, Moderate Persistent", "J45.40", "managed", "Well-controlled on fluticasone/salmeterol."),
                ("Polycystic Ovary Syndrome", "E28.2", "active", "Irregular menses. On oral contraceptive for regulation."),
                ("Vitamin B12 Deficiency", "E53.8", "active", "Monthly B12 injections."),
            ],
            "allergies": [
                ("Dust mites", "Wheezing, nasal congestion", "moderate"),
                ("Amoxicillin", "Rash", "mild"),
            ],
            "medications": [
                ("Fluticasone/Salmeterol", "250/50 mcg", "Twice daily inhaled", "inhalation", "Asthma controller"),
                ("Albuterol", "90 mcg", "PRN 2 puffs", "inhalation", "Asthma rescue"),
                ("Norgestimate/Ethinyl Estradiol", "0.25/0.035 mg", "Once daily", "oral", "PCOS and contraception"),
                ("Cyanocobalamin", "1000 mcg", "Monthly injection", "intramuscular", "B12 deficiency"),
            ],
        },
        {
            "email": "patient.garcia@demo.dev",
            "first_name": "Carlos",
            "last_name": "Garcia",
            "phone": "+1-555-301-0006",
            "dob": date(1980, 9, 12),
            "gender": "Male",
            "blood_type": "O-",
            "height_cm": Decimal("172.0"),
            "weight_kg": Decimal("78.5"),
            "emergency_contact": {"name": "Ana Garcia", "phone": "+1-555-301-9006", "relationship": "Wife"},
            "insurance_info": {"provider": "Humana", "policy_number": "HUM-6621847", "group_number": "GRP-3302"},
            "conditions": [
                ("Major Depressive Disorder, Recurrent", "F33.1", "managed", "Stable on bupropion. Sees therapist biweekly."),
                ("Gastroesophageal Reflux Disease", "K21.0", "managed", "Omeprazole and dietary modifications."),
                ("Chronic Low Back Pain", "M54.5", "chronic", "Lumbar disc degeneration. Physical therapy ongoing."),
            ],
            "allergies": [
                ("NSAIDs", "GI ulceration", "moderate"),
                ("Bee stings", "Local swelling, mild anaphylaxis", "severe"),
            ],
            "medications": [
                ("Bupropion XL", "300 mg", "Once daily", "oral", "Depression management"),
                ("Omeprazole", "20 mg", "Once daily before breakfast", "oral", "GERD"),
                ("Cyclobenzaprine", "10 mg", "PRN at bedtime", "oral", "Muscle spasm relief"),
                ("Acetaminophen", "500 mg", "Every 6 hours PRN", "oral", "Back pain"),
            ],
        },
        {
            "email": "patient.oconnor@demo.dev",
            "first_name": "Siobhan",
            "last_name": "O'Connor",
            "phone": "+1-555-301-0007",
            "dob": date(1955, 12, 3),
            "gender": "Female",
            "blood_type": "B-",
            "height_cm": Decimal("160.0"),
            "weight_kg": Decimal("68.0"),
            "emergency_contact": {"name": "Patrick O'Connor", "phone": "+1-555-301-9007", "relationship": "Son"},
            "insurance_info": {"provider": "Medicare", "policy_number": "MCR-8894561", "group_number": "N/A"},
            "conditions": [
                ("Atrial Fibrillation", "I48.91", "chronic", "Paroxysmal AFib. On apixaban anticoagulation."),
                ("Osteoporosis", "M81.0", "managed", "T-score -2.8 at lumbar spine. On alendronate."),
                ("Hypothyroidism", "E03.9", "managed", "TSH normalized on levothyroxine."),
                ("Osteoarthritis of Knee", "M17.11", "chronic", "Bilateral. Conservative management with PT."),
                ("Mild Cognitive Impairment", "G31.84", "active", "Under observation. Annual cognitive screening."),
            ],
            "allergies": [
                ("Morphine", "Respiratory depression, severe sedation", "severe"),
                ("Sulfa drugs", "Stevens-Johnson syndrome history", "life_threatening"),
                ("Peanuts", "Anaphylaxis", "life_threatening"),
            ],
            "medications": [
                ("Apixaban", "5 mg", "Twice daily", "oral", "Anticoagulation for AFib"),
                ("Alendronate", "70 mg", "Once weekly", "oral", "Osteoporosis"),
                ("Levothyroxine", "75 mcg", "Once daily on empty stomach", "oral", "Hypothyroidism"),
                ("Acetaminophen", "650 mg", "Every 8 hours PRN", "oral", "Osteoarthritis pain"),
                ("Calcium/Vitamin D", "600 mg/400 IU", "Twice daily", "oral", "Bone health"),
            ],
        },
        {
            "email": "patient.nguyen@demo.dev",
            "first_name": "Thanh",
            "last_name": "Nguyen",
            "phone": "+1-555-301-0008",
            "dob": date(1990, 4, 25),
            "gender": "Male",
            "blood_type": "A+",
            "height_cm": Decimal("170.0"),
            "weight_kg": Decimal("72.0"),
            "emergency_contact": {"name": "Linh Nguyen", "phone": "+1-555-301-9008", "relationship": "Sister"},
            "insurance_info": {"provider": "Anthem Blue Cross", "policy_number": "ANT-4459182", "group_number": "GRP-7704"},
            "conditions": [
                ("Crohn's Disease", "K50.10", "active", "Ileal involvement. Currently on adalimumab."),
                ("Iron Deficiency Anemia", "D50.9", "active", "Secondary to Crohn's. IV iron infusions."),
                ("Anxiety Disorder", "F41.9", "managed", "Low-dose buspirone effective."),
            ],
            "allergies": [
                ("Metronidazole", "Peripheral neuropathy", "moderate"),
                ("Ciprofloxacin", "Tendon pain", "moderate"),
            ],
            "medications": [
                ("Adalimumab", "40 mg", "Every 2 weeks", "subcutaneous", "Crohn's disease"),
                ("Iron Sucrose", "200 mg", "IV every 4 weeks", "intravenous", "Iron deficiency anemia"),
                ("Buspirone", "10 mg", "Twice daily", "oral", "Anxiety"),
                ("Folic Acid", "1 mg", "Once daily", "oral", "Nutritional support"),
            ],
        },
        {
            "email": "patient.jackson@demo.dev",
            "first_name": "Aaliyah",
            "last_name": "Jackson",
            "phone": "+1-555-301-0009",
            "dob": date(2000, 8, 9),
            "gender": "Female",
            "blood_type": "O+",
            "height_cm": Decimal("168.0"),
            "weight_kg": Decimal("59.0"),
            "emergency_contact": {"name": "Denise Jackson", "phone": "+1-555-301-9009", "relationship": "Mother"},
            "insurance_info": {"provider": "Molina Healthcare", "policy_number": "MOL-2238476", "group_number": "GRP-9901"},
            "conditions": [
                ("Type 1 Diabetes Mellitus", "E10.9", "chronic", "Diagnosed age 12. Insulin pump therapy."),
                ("Celiac Disease", "K90.0", "managed", "Strict gluten-free diet."),
                ("Eczema", "L30.9", "active", "Flares on hands and arms. Topical steroids."),
            ],
            "allergies": [
                ("Gluten", "GI distress, malabsorption", "severe"),
                ("Nickel", "Contact dermatitis", "mild"),
            ],
            "medications": [
                ("Insulin Lispro", "Variable dose", "With meals via pump", "subcutaneous", "Mealtime insulin for T1D"),
                ("Insulin Glargine", "18 units", "Once daily", "subcutaneous", "Basal insulin for T1D"),
                ("Triamcinolone Acetonide", "0.1% cream", "Twice daily to affected areas", "topical", "Eczema flares"),
                ("Cetirizine", "10 mg", "Once daily", "oral", "Eczema-related itching"),
            ],
        },
        {
            "email": "patient.mueller@demo.dev",
            "first_name": "Hans",
            "last_name": "Mueller",
            "phone": "+1-555-301-0010",
            "dob": date(1970, 6, 17),
            "gender": "Male",
            "blood_type": "AB-",
            "height_cm": Decimal("185.0"),
            "weight_kg": Decimal("102.0"),
            "emergency_contact": {"name": "Greta Mueller", "phone": "+1-555-301-9010", "relationship": "Wife"},
            "insurance_info": {"provider": "Cigna", "policy_number": "CIG-9917352", "group_number": "GRP-2208"},
            "conditions": [
                ("Essential Hypertension", "I10", "managed", "On amlodipine and losartan."),
                ("Type 2 Diabetes Mellitus", "E11.65", "managed", "HbA1c 7.1%. On metformin and empagliflozin."),
                ("Gout", "M10.9", "active", "Recurrent flares. Allopurinol prophylaxis."),
                ("Non-alcoholic Fatty Liver Disease", "K76.0", "active", "Grade 2 steatosis on ultrasound."),
            ],
            "allergies": [
                ("Lisinopril", "Persistent dry cough", "moderate"),
                ("Allopurinol (initial dose)", "Gout flare exacerbation", "mild"),
            ],
            "medications": [
                ("Amlodipine", "5 mg", "Once daily", "oral", "Hypertension"),
                ("Losartan", "50 mg", "Once daily", "oral", "Hypertension and renal protection"),
                ("Metformin", "1000 mg", "Twice daily", "oral", "Type 2 Diabetes"),
                ("Empagliflozin", "10 mg", "Once daily", "oral", "Diabetes and cardiovascular benefit"),
                ("Allopurinol", "300 mg", "Once daily", "oral", "Gout prophylaxis"),
            ],
        },
    ]

    patient_users: list[User] = []
    patient_profiles: list[PatientProfile] = []

    for idx, pd in enumerate(patients_raw):
        # Assign doctors round-robin
        assigned_doctor = doctor_users[idx % len(doctor_users)]

        u = User(
            email=pd["email"],
            first_name=pd["first_name"],
            last_name=pd["last_name"],
            role="patient",
            phone=pd["phone"],
            is_active=True,
            is_verified=True,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.flush()

        pp = PatientProfile(
            user_id=u.id,
            date_of_birth=pd["dob"],
            gender=pd["gender"],
            blood_type=pd["blood_type"],
            height_cm=pd["height_cm"],
            weight_kg=pd["weight_kg"],
            emergency_contact=pd["emergency_contact"],
            insurance_info=pd["insurance_info"],
            assigned_doctor_id=assigned_doctor.id,
        )
        db.session.add(pp)
        db.session.flush()

        patient_users.append(u)
        patient_profiles.append(pp)

        # ---- Medical History ----
        for cond_name, icd10, status, notes in pd["conditions"]:
            mh = MedicalHistory(
                patient_id=pp.id,
                condition_name=cond_name,
                diagnosis_date=today - timedelta(days=random.randint(90, 1800)),
                status=status,
                icd_10_code=icd10,
                notes=notes,
                diagnosed_by=assigned_doctor.id,
                created_by=assigned_doctor.id,
            )
            db.session.add(mh)

        # ---- Allergies ----
        for allergen, reaction, severity in pd["allergies"]:
            al = Allergy(
                patient_id=pp.id,
                allergen=allergen,
                reaction=reaction,
                severity=severity,
                diagnosed_date=today - timedelta(days=random.randint(365, 3650)),
                created_by=assigned_doctor.id,
            )
            db.session.add(al)

        # ---- Medications ----
        for med_name, dosage, frequency, route, reason in pd["medications"]:
            med = Medication(
                patient_id=u.id,
                name=med_name,
                dosage=dosage,
                frequency=frequency,
                route=route,
                prescribed_by=assigned_doctor.id,
                start_date=today - timedelta(days=random.randint(30, 365)),
                end_date=None,
                status="active",
                reason=reason,
                side_effects=None,
                refills_remaining=random.randint(0, 6),
                pharmacy_notes=None,
                created_by=assigned_doctor.id,
            )
            db.session.add(med)

        # ---- Vitals Readings (12 over last 7 days) ----
        base_hr = random.randint(65, 85)
        base_sys = random.randint(110, 135)
        base_dia = random.randint(65, 85)
        base_temp = Decimal("36.6") + Decimal(str(round(random.uniform(-0.3, 0.5), 1)))
        base_spo2 = Decimal("97.0") + Decimal(str(round(random.uniform(-1.0, 2.0), 1)))
        base_rr = random.randint(14, 18)
        base_glucose = Decimal("95.0") + Decimal(str(round(random.uniform(-10, 30), 1)))

        for v_idx in range(12):
            hours_ago = random.randint(1, 168)  # within 7 days
            recorded = now - timedelta(hours=hours_ago)

            hr = base_hr + random.randint(-8, 12)
            sys_bp = base_sys + random.randint(-10, 15)
            dia_bp = base_dia + random.randint(-8, 10)
            temp = base_temp + Decimal(str(round(random.uniform(-0.3, 0.4), 2)))
            spo2 = min(Decimal("100.0"), base_spo2 + Decimal(str(round(random.uniform(-1.5, 1.5), 1))))
            rr = base_rr + random.randint(-2, 4)
            glucose = base_glucose + Decimal(str(round(random.uniform(-8, 12), 1)))
            pain = random.choice([0, 0, 0, 1, 2, 3])

            vr = VitalsReading(
                patient_id=u.id,
                heart_rate=hr,
                blood_pressure_systolic=sys_bp,
                blood_pressure_diastolic=dia_bp,
                temperature=temp,
                oxygen_saturation=spo2,
                respiratory_rate=rr,
                blood_glucose=glucose,
                weight_kg=pd["weight_kg"],
                pain_level=pain,
                device_id=None,
                is_manual_entry=True,
                is_anomalous=False,
                notes=None,
                recorded_at=recorded,
                created_by=u.id,
            )
            db.session.add(vr)

        # ---- Appointments (3 per patient) ----
        # 1. Completed appointment in the past
        appt_past = Appointment(
            patient_id=u.id,
            doctor_id=assigned_doctor.id,
            appointment_type="in_person",
            status="completed",
            scheduled_at=now - timedelta(days=random.randint(7, 30)),
            duration_minutes=30,
            reason="Routine follow-up and lab review",
            notes="Patient vitals stable. Continue current medications. Recheck in 3 months.",
            created_by=u.id,
        )
        db.session.add(appt_past)

        # 2. Upcoming appointment
        appt_upcoming = Appointment(
            patient_id=u.id,
            doctor_id=assigned_doctor.id,
            appointment_type=random.choice(["in_person", "telemedicine"]),
            status="scheduled",
            scheduled_at=now + timedelta(days=random.randint(3, 21)),
            duration_minutes=30,
            reason=random.choice([
                "Quarterly diabetes check-up",
                "Medication review and adjustment",
                "Follow-up on recent lab results",
                "Annual wellness visit",
                "Blood pressure monitoring",
            ]),
            notes=None,
            created_by=u.id,
        )
        db.session.add(appt_upcoming)

        # 3. Another appointment (mix of scheduled / completed)
        if idx % 2 == 0:
            appt_extra = Appointment(
                patient_id=u.id,
                doctor_id=doctor_users[(idx + 1) % len(doctor_users)].id,
                appointment_type="telemedicine",
                status="completed",
                scheduled_at=now - timedelta(days=random.randint(14, 60)),
                duration_minutes=20,
                reason="Specialist consultation referral",
                notes="Discussed treatment options. Recommend continuing current plan.",
                created_by=u.id,
            )
        else:
            appt_extra = Appointment(
                patient_id=u.id,
                doctor_id=doctor_users[(idx + 1) % len(doctor_users)].id,
                appointment_type="follow_up",
                status="scheduled",
                scheduled_at=now + timedelta(days=random.randint(7, 45)),
                duration_minutes=15,
                reason="Follow-up on specialist referral",
                notes=None,
                created_by=u.id,
            )
        db.session.add(appt_extra)

        # ---- Medical Reports (2 per patient) ----
        # Report 1: CBC lab report
        report_date_1 = now - timedelta(days=random.randint(5, 30))
        report1 = MedicalReport(
            patient_id=u.id,
            report_type="lab",
            title="Complete Blood Count (CBC)",
            content="Routine CBC panel ordered as part of periodic health assessment.",
            file_url=None,
            file_type="pdf",
            ai_summary=(
                f"CBC results for {pd['first_name']} {pd['last_name']} are largely within normal limits. "
                "White blood cell count, hemoglobin, and platelet count are all within reference ranges. "
                "No significant abnormalities detected."
            ),
            ai_analysis={
                "overall_assessment": "Normal",
                "abnormal_count": 0,
                "findings": [
                    "All CBC values within normal reference ranges",
                    "No signs of infection or anemia",
                    "Platelet count adequate for normal hemostasis",
                ],
                "recommendations": ["Routine follow-up in 6-12 months"],
            },
            status="completed",
            reviewed_by=assigned_doctor.id,
            reviewed_at=report_date_1 + timedelta(hours=4),
            created_by=u.id,
            created_at=report_date_1,
        )
        db.session.add(report1)
        db.session.flush()

        # Lab values for CBC
        cbc_values = [
            ("White Blood Cell Count", Decimal("6.8"), "10^3/uL", Decimal("4.5"), Decimal("11.0"), False, "26464-8"),
            ("Red Blood Cell Count", Decimal("4.75"), "10^6/uL", Decimal("4.2"), Decimal("5.9"), False, "789-8"),
            ("Hemoglobin", Decimal("14.2"), "g/dL", Decimal("12.0"), Decimal("17.5"), False, "718-7"),
            ("Hematocrit", Decimal("42.1"), "%", Decimal("36.0"), Decimal("51.0"), False, "4544-3"),
            ("Platelet Count", Decimal("245.0"), "10^3/uL", Decimal("150.0"), Decimal("400.0"), False, "777-3"),
            ("Mean Corpuscular Volume", Decimal("88.6"), "fL", Decimal("80.0"), Decimal("100.0"), False, "787-2"),
        ]
        for test_name, val, unit, ref_min, ref_max, abnormal, loinc in cbc_values:
            lv = LabValue(
                report_id=report1.id,
                patient_id=u.id,
                test_name=test_name,
                value=val + Decimal(str(round(random.uniform(-0.5, 0.5), 2))),
                unit=unit,
                reference_min=ref_min,
                reference_max=ref_max,
                is_abnormal=abnormal,
                loinc_code=loinc,
                collected_at=report_date_1 - timedelta(hours=2),
            )
            db.session.add(lv)

        # Report 2: Metabolic Panel
        report_date_2 = now - timedelta(days=random.randint(10, 45))
        report2 = MedicalReport(
            patient_id=u.id,
            report_type="lab",
            title="Comprehensive Metabolic Panel (CMP)",
            content="CMP ordered for metabolic screening and medication monitoring.",
            file_url=None,
            file_type="pdf",
            ai_summary=(
                f"Comprehensive Metabolic Panel for {pd['first_name']} {pd['last_name']}. "
                "Kidney function markers (BUN, creatinine) within normal limits. "
                "Liver enzymes within acceptable range. Electrolytes balanced."
            ),
            ai_analysis={
                "overall_assessment": "Normal with minor notes",
                "abnormal_count": 1,
                "findings": [
                    "Kidney function normal (eGFR > 90)",
                    "Liver enzymes within normal range",
                    "Fasting glucose slightly elevated — correlates with known diabetes",
                ],
                "recommendations": [
                    "Continue monitoring glucose as per diabetes management plan",
                    "Repeat CMP in 3-6 months",
                ],
            },
            status="completed",
            reviewed_by=assigned_doctor.id,
            reviewed_at=report_date_2 + timedelta(hours=6),
            created_by=u.id,
            created_at=report_date_2,
        )
        db.session.add(report2)
        db.session.flush()

        cmp_values = [
            ("Glucose, Fasting", Decimal("108.0"), "mg/dL", Decimal("70.0"), Decimal("100.0"), True, "2345-7"),
            ("BUN", Decimal("16.0"), "mg/dL", Decimal("7.0"), Decimal("20.0"), False, "3094-0"),
            ("Creatinine", Decimal("0.95"), "mg/dL", Decimal("0.6"), Decimal("1.2"), False, "2160-0"),
            ("Sodium", Decimal("140.0"), "mEq/L", Decimal("136.0"), Decimal("145.0"), False, "2951-2"),
            ("Potassium", Decimal("4.2"), "mEq/L", Decimal("3.5"), Decimal("5.1"), False, "2823-3"),
            ("Calcium", Decimal("9.4"), "mg/dL", Decimal("8.5"), Decimal("10.5"), False, "17861-6"),
            ("ALT", Decimal("28.0"), "U/L", Decimal("7.0"), Decimal("56.0"), False, "1742-6"),
            ("AST", Decimal("24.0"), "U/L", Decimal("10.0"), Decimal("40.0"), False, "1920-8"),
        ]
        for test_name, val, unit, ref_min, ref_max, abnormal, loinc in cmp_values:
            lv = LabValue(
                report_id=report2.id,
                patient_id=u.id,
                test_name=test_name,
                value=val + Decimal(str(round(random.uniform(-2.0, 2.0), 2))),
                unit=unit,
                reference_min=ref_min,
                reference_max=ref_max,
                is_abnormal=abnormal,
                loinc_code=loinc,
                collected_at=report_date_2 - timedelta(hours=3),
            )
            db.session.add(lv)

        # ---- Care Plan (1 per patient) ----
        condition_for_plan = pd["conditions"][0][0]
        cp = CarePlan(
            patient_id=u.id,
            doctor_id=assigned_doctor.id,
            title=f"{condition_for_plan} Management Plan",
            description=f"Comprehensive care plan for managing {condition_for_plan}. Includes medication adherence, lifestyle modifications, and regular monitoring.",
            status="active",
            start_date=today - timedelta(days=random.randint(30, 90)),
            end_date=today + timedelta(days=180),
            ai_recommendations={
                "lifestyle": [
                    "Maintain balanced diet appropriate for condition",
                    "Regular moderate exercise 150 minutes per week",
                    "Adequate sleep (7-9 hours per night)",
                    "Stress management through mindfulness or relaxation techniques",
                ],
                "monitoring": [
                    "Regular vital sign monitoring",
                    "Follow-up labs every 3 months",
                    "Report any new or worsening symptoms promptly",
                ],
            },
            created_by=assigned_doctor.id,
        )
        db.session.add(cp)
        db.session.flush()

        # Care plan goals
        goal1 = CarePlanGoal(
            care_plan_id=cp.id,
            title="Medication Adherence",
            description="Take all prescribed medications as directed without missing doses.",
            target_value="95",
            current_value=str(random.randint(80, 98)),
            unit="% adherence",
            status="in_progress",
            target_date=today + timedelta(days=90),
        )
        db.session.add(goal1)
        db.session.flush()

        goal2 = CarePlanGoal(
            care_plan_id=cp.id,
            title="Blood Pressure Target",
            description="Maintain systolic blood pressure below 140 mmHg and diastolic below 90 mmHg.",
            target_value="<140/90",
            current_value=f"{base_sys}/{base_dia}",
            unit="mmHg",
            status="in_progress",
            target_date=today + timedelta(days=90),
        )
        db.session.add(goal2)
        db.session.flush()

        # Care plan activities
        activities_data = [
            ("Take morning medications", "Take prescribed morning medications with breakfast", "medication", "Daily", goal1.id),
            ("30-minute walk", "Moderate-intensity walking for cardiovascular health", "exercise", "5 times per week", None),
            ("Blood pressure check", "Measure and record blood pressure at home", "monitoring", "Twice daily", goal2.id),
            ("Follow-up appointment", "Attend scheduled follow-up with primary care physician", "appointment", "Every 3 months", None),
        ]
        for act_title, act_desc, act_type, freq, gid in activities_data:
            act = CarePlanActivity(
                care_plan_id=cp.id,
                goal_id=gid,
                title=act_title,
                description=act_desc,
                activity_type=act_type,
                frequency=freq,
                status=random.choice(["pending", "in_progress", "completed"]),
                due_date=now + timedelta(days=random.randint(1, 30)),
                completed_at=now - timedelta(days=1) if random.random() > 0.5 else None,
            )
            db.session.add(act)

    db.session.flush()

    # ------------------------------------------------------------------ #
    # 4. Monitoring Alerts (8 alerts across different patients)
    # ------------------------------------------------------------------ #
    alert_definitions = [
        {
            "patient_idx": 1,  # Marcus Williams - cardiac patient
            "alert_type": "heart_rate",
            "severity": "high",
            "title": "Elevated Heart Rate Detected",
            "description": "Heart rate of 112 bpm recorded, exceeding the upper threshold of 100 bpm. Patient has history of coronary artery disease.",
            "status": "acknowledged",
            "escalation_level": 1,
        },
        {
            "patient_idx": 3,  # David Thompson - COPD
            "alert_type": "oxygen_saturation",
            "severity": "critical",
            "title": "Low Oxygen Saturation Alert",
            "description": "SpO2 dropped to 89%, below critical threshold of 92%. Patient has COPD. Immediate assessment recommended.",
            "status": "active",
            "escalation_level": 2,
        },
        {
            "patient_idx": 0,  # Emily Johnson - diabetic
            "alert_type": "blood_glucose",
            "severity": "medium",
            "title": "Elevated Fasting Blood Glucose",
            "description": "Fasting blood glucose of 185 mg/dL recorded. Patient has Type 2 Diabetes. Consider medication adjustment.",
            "status": "resolved",
            "escalation_level": 0,
        },
        {
            "patient_idx": 6,  # Siobhan O'Connor - AFib
            "alert_type": "heart_rate",
            "severity": "high",
            "title": "Irregular Heart Rate Pattern",
            "description": "Heart rate variability suggests possible atrial fibrillation episode. Rate of 128 bpm with irregular rhythm.",
            "status": "active",
            "escalation_level": 1,
        },
        {
            "patient_idx": 9,  # Hans Mueller - hypertension
            "alert_type": "blood_pressure",
            "severity": "high",
            "title": "Hypertensive Reading",
            "description": "Blood pressure of 178/105 mmHg recorded. Exceeds stage 2 hypertension threshold. Patient on amlodipine and losartan.",
            "status": "acknowledged",
            "escalation_level": 1,
        },
        {
            "patient_idx": 8,  # Aaliyah Jackson - T1D
            "alert_type": "blood_glucose",
            "severity": "critical",
            "title": "Hypoglycemic Episode",
            "description": "Blood glucose dropped to 52 mg/dL. Patient has Type 1 Diabetes on insulin pump. Immediate intervention needed.",
            "status": "resolved",
            "escalation_level": 2,
        },
        {
            "patient_idx": 4,  # Soo-Jin Kim - asthma
            "alert_type": "respiratory_rate",
            "severity": "medium",
            "title": "Elevated Respiratory Rate",
            "description": "Respiratory rate of 26 breaths/min detected. Patient has moderate persistent asthma.",
            "status": "active",
            "escalation_level": 0,
        },
        {
            "patient_idx": 7,  # Thanh Nguyen - Crohn's
            "alert_type": "temperature",
            "severity": "medium",
            "title": "Low-Grade Fever Detected",
            "description": "Temperature of 38.1 C recorded. Patient on adalimumab (immunosuppressant). Monitor for infection.",
            "status": "active",
            "escalation_level": 0,
        },
    ]

    for ad in alert_definitions:
        p_user = patient_users[ad["patient_idx"]]
        p_doctor = doctor_users[ad["patient_idx"] % len(doctor_users)]
        created_time = now - timedelta(hours=random.randint(1, 48))

        alert = MonitoringAlert(
            patient_id=p_user.id,
            vitals_reading_id=None,
            alert_type=ad["alert_type"],
            severity=ad["severity"],
            title=ad["title"],
            description=ad["description"],
            resolution_notes="Resolved after clinical assessment. Vitals returned to normal range." if ad["status"] == "resolved" else None,
            ai_analysis={
                "risk_level": ad["severity"],
                "recommendation": "Continue monitoring" if ad["severity"] in ("low", "medium") else "Clinical assessment recommended",
                "context": f"Alert generated based on vitals threshold breach for {ad['alert_type']}.",
            },
            status=ad["status"],
            acknowledged_by=p_doctor.id if ad["status"] in ("acknowledged", "resolved") else None,
            acknowledged_at=created_time + timedelta(minutes=random.randint(2, 15)) if ad["status"] in ("acknowledged", "resolved") else None,
            resolved_by=p_doctor.id if ad["status"] == "resolved" else None,
            resolved_at=created_time + timedelta(minutes=random.randint(20, 60)) if ad["status"] == "resolved" else None,
            escalation_level=ad["escalation_level"],
            escalated_at=created_time + timedelta(minutes=5) if ad["escalation_level"] > 0 else None,
            created_at=created_time,
        )
        db.session.add(alert)

    # ------------------------------------------------------------------ #
    # 5. Notifications
    # ------------------------------------------------------------------ #
    notification_templates = [
        ("alert", "Vital Sign Alert", "A new vital sign alert has been generated for one of your patients."),
        ("appointment", "Upcoming Appointment Reminder", "You have an appointment scheduled in the next 24 hours."),
        ("report", "Lab Results Available", "New lab results are available for review."),
        ("medication", "Medication Reminder", "It's time to take your scheduled medication."),
        ("care_plan", "Care Plan Update", "Your care plan has been updated by your physician."),
        ("system", "Welcome to MedAssist AI", "Your account has been set up successfully. Explore the platform to manage your health."),
    ]

    # Notifications for patients
    for p_user in patient_users:
        for n_type, n_title, n_message in random.sample(notification_templates, k=random.randint(2, 4)):
            notif = Notification(
                user_id=p_user.id,
                type=n_type,
                title=n_title,
                message=n_message,
                data={"source": "system"},
                read=random.choice([True, False]),
                read_at=now - timedelta(hours=random.randint(1, 48)) if random.random() > 0.5 else None,
                channel="in_app",
                sent_at=now - timedelta(hours=random.randint(1, 72)),
            )
            db.session.add(notif)

    # Notifications for doctors
    for d_user in doctor_users:
        for _ in range(3):
            n_type, n_title, n_message = random.choice(notification_templates[:2])
            notif = Notification(
                user_id=d_user.id,
                type=n_type,
                title=n_title,
                message=n_message,
                data={"source": "monitoring_system"},
                read=random.choice([True, False]),
                read_at=now - timedelta(hours=random.randint(1, 24)) if random.random() > 0.5 else None,
                channel="in_app",
                sent_at=now - timedelta(hours=random.randint(1, 48)),
            )
            db.session.add(notif)

    # ------------------------------------------------------------------ #
    # Commit everything
    # ------------------------------------------------------------------ #
    db.session.commit()

    total_users = User.query.count()
    print(f"Seeded {total_users} users (3 doctors, 1 admin, 10 patients)")
    print("Seeded patient profiles, medical history, allergies, medications")
    print("Seeded vitals readings, appointments, medical reports with lab values")
    print("Seeded care plans with goals and activities")
    print("Seeded monitoring alerts and notifications")
    print("Demo seed complete.")


# Auto-create tables on startup (needed for Render free tier — no shell access)
with app.app_context():
    db.create_all()

    # Auto-seed demo data if DB is empty (use advisory lock to prevent race between workers)
    from app.models.user import User
    try:
        got_lock = db.session.execute(db.text("SELECT pg_try_advisory_lock(12345)")).scalar()
        if got_lock and User.query.count() == 0:
            print("Empty database detected — seeding comprehensive demo data...")
            _seed_all_demo_data()
        if got_lock:
            db.session.execute(db.text("SELECT pg_advisory_unlock(12345)"))
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Seed error (non-fatal): {e}")

if __name__ == "__main__":
    app.run()
