"""Seed additional data to ensure all tables have 100+ records.

Run from backend/:
    DATABASE_URL=postgresql://medassist:medassist_dev@localhost:5499/medassist python scripts/seed_extra_data.py
"""

import os
import sys
import uuid
import random
import json
from datetime import datetime, timedelta, date, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://medassist:medassist_dev@localhost:5499/medassist",
)

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app("development")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def random_past(days_back: int = 180) -> datetime:
    return now_utc() - timedelta(
        days=random.randint(1, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )


def random_future(days_ahead: int = 60) -> datetime:
    return now_utc() + timedelta(
        days=random.randint(1, days_ahead),
        hours=random.randint(8, 17),
        minutes=random.choice([0, 15, 30, 45]),
    )


def uid() -> str:
    return str(uuid.uuid4())


def seed() -> None:
    with app.app_context():
        # --- Fetch existing IDs ------------------------------------------------
        patient_user_ids = [
            r[0]
            for r in db.session.execute(
                text("SELECT id FROM users WHERE role = 'patient'")
            )
        ]
        doctor_user_ids = [
            r[0]
            for r in db.session.execute(
                text("SELECT id FROM users WHERE role = 'doctor'")
            )
        ]
        nurse_user_ids = [
            r[0]
            for r in db.session.execute(
                text("SELECT id FROM users WHERE role = 'nurse'")
            )
        ]
        all_user_ids = patient_user_ids + doctor_user_ids + nurse_user_ids
        report_rows = list(
            db.session.execute(
                text("SELECT id, patient_id FROM medical_reports")
            )
        )
        vitals_rows = list(
            db.session.execute(
                text("SELECT id, patient_id FROM vitals_readings")
            )
        )
        existing_appointment_ids = [
            r[0]
            for r in db.session.execute(text("SELECT id FROM appointments"))
        ]

        n = now_utc()

        # --- 1. Devices (100 new) ---------------------------------------------
        print("Seeding devices...")
        device_types = [
            "heart_rate_monitor", "blood_pressure_cuff", "pulse_oximeter",
            "thermometer", "glucose_monitor", "weight_scale",
            "ecg_monitor", "spirometer", "activity_tracker", "smartwatch",
        ]
        manufacturers = [
            "Withings", "Omron", "Masimo", "Philips", "Dexcom",
            "Garmin", "Fitbit", "Apple", "Samsung", "Medtronic",
        ]
        for i in range(100):
            dt = device_types[i % len(device_types)]
            mfr = manufacturers[i % len(manufacturers)]
            db.session.execute(
                text("""
                    INSERT INTO devices
                        (id, patient_id, device_type, device_name, manufacturer,
                         model, serial_number, firmware_version, status,
                         last_sync_at, battery_level, configuration, created_at, updated_at)
                    VALUES
                        (:id, :pid, :dtype, :dname, :mfr, :mdl, :sn, :fw, :st,
                         :sync, :batt, :cfg, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": str(random.choice(patient_user_ids)),
                    "dtype": dt,
                    "dname": f"{mfr} {dt.replace('_', ' ').title()} {i+1}",
                    "mfr": mfr,
                    "mdl": f"Model-{random.randint(100, 999)}",
                    "sn": f"SN-{uuid.uuid4().hex[:12].upper()}",
                    "fw": f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}",
                    "st": random.choice(["active", "active", "active", "inactive", "maintenance"]),
                    "sync": random_past(30),
                    "batt": random.randint(10, 100),
                    "cfg": json.dumps({"interval_seconds": random.choice([30, 60, 120, 300])}),
                    "ca": random_past(365),
                    "ua": random_past(30),
                },
            )
        db.session.commit()
        print("  devices: 100 inserted")

        # --- 2. Appointments (need 70 more -> seed 80 to be safe) -------------
        print("Seeding appointments...")
        appt_types = ["in_person", "telemedicine", "follow_up", "emergency"]
        appt_statuses = ["scheduled", "confirmed", "completed", "cancelled", "no_show"]
        reasons = [
            "Annual check-up", "Follow-up visit", "Chest pain evaluation",
            "Blood pressure review", "Diabetes management", "Medication review",
            "Post-surgery follow-up", "Persistent cough", "Headache evaluation",
            "Joint pain assessment", "Skin rash consultation", "Lab result review",
            "Vaccination", "Weight management", "Mental health check-in",
        ]
        new_appt_ids = []
        for i in range(80):
            aid = uid()
            new_appt_ids.append(aid)
            pid = str(random.choice(patient_user_ids))
            did = str(random.choice(doctor_user_ids))
            atype = random.choice(appt_types)
            status = random.choice(appt_statuses)
            sched = random_past(90) if status in ("completed", "cancelled", "no_show") else random_future(60)
            db.session.execute(
                text("""
                    INSERT INTO appointments
                        (id, patient_id, doctor_id, appointment_type, status,
                         scheduled_at, duration_minutes, reason, notes, created_by,
                         created_at, updated_at)
                    VALUES
                        (:id, :pid, :did, :atype, :status, :sched, :dur, :reason,
                         :notes, :cb, :ca, :ua)
                """),
                {
                    "id": aid,
                    "pid": pid,
                    "did": did,
                    "atype": atype,
                    "status": status,
                    "sched": sched,
                    "dur": random.choice([15, 30, 30, 45, 60]),
                    "reason": random.choice(reasons),
                    "notes": f"Auto-seeded appointment #{i+1}",
                    "cb": pid,
                    "ca": random_past(120),
                    "ua": random_past(30),
                },
            )
        db.session.commit()
        print("  appointments: 80 inserted")

        # --- 3. Telemedicine sessions (100 new) --------------------------------
        print("Seeding telemedicine sessions...")
        # Use both existing + new appointments
        all_appt_ids = existing_appointment_ids + new_appt_ids
        tele_statuses = ["waiting", "in_progress", "completed", "completed", "completed"]
        for i in range(100):
            aid = str(random.choice(all_appt_ids))
            pid = str(random.choice(patient_user_ids))
            did = str(random.choice(doctor_user_ids))
            status = random.choice(tele_statuses)
            started = random_past(90)
            dur = random.randint(300, 3600)
            ended = started + timedelta(seconds=dur) if status == "completed" else None
            db.session.execute(
                text("""
                    INSERT INTO telemedicine_sessions
                        (id, appointment_id, patient_id, doctor_id, room_url,
                         room_token, status, started_at, ended_at, duration_seconds,
                         recording_url, ai_transcript, ai_summary, created_at, updated_at)
                    VALUES
                        (:id, :aid, :pid, :did, :room, :token, :st, :start, :end,
                         :dur, :rec, :trans, :summ, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "aid": aid,
                    "pid": pid,
                    "did": did,
                    "room": f"https://medassist.daily.co/room-{uuid.uuid4().hex[:8]}",
                    "token": f"tok_{uuid.uuid4().hex}",
                    "st": status,
                    "start": started if status != "waiting" else None,
                    "end": ended,
                    "dur": dur if status == "completed" else None,
                    "rec": None,
                    "trans": f"Sample transcript for session {i+1}" if status == "completed" else None,
                    "summ": f"Patient discussed symptoms. Follow-up planned." if status == "completed" else None,
                    "ca": started - timedelta(minutes=15),
                    "ua": ended or started,
                },
            )
        db.session.commit()
        print("  telemedicine_sessions: 100 inserted")

        # --- 4. Monitoring alerts (90 more) ------------------------------------
        print("Seeding monitoring alerts...")
        alert_types = [
            "heart_rate_high", "heart_rate_low", "bp_high", "bp_low",
            "spo2_low", "temperature_high", "respiratory_rate_high",
            "glucose_high", "glucose_low", "weight_change",
        ]
        severities = ["low", "medium", "high", "critical"]
        alert_statuses = ["active", "acknowledged", "resolved", "dismissed"]
        for i in range(90):
            atype = random.choice(alert_types)
            sev = random.choice(severities)
            status = random.choice(alert_statuses)
            pid = str(random.choice(patient_user_ids))
            vid = str(random.choice(vitals_rows)[0]) if vitals_rows else None
            created = random_past(60)
            ack_by = str(random.choice(nurse_user_ids + doctor_user_ids)) if status in ("acknowledged", "resolved") else None
            ack_at = created + timedelta(minutes=random.randint(1, 30)) if ack_by else None
            res_by = str(random.choice(doctor_user_ids)) if status == "resolved" else None
            res_at = (ack_at or created) + timedelta(minutes=random.randint(5, 120)) if res_by else None
            db.session.execute(
                text("""
                    INSERT INTO monitoring_alerts
                        (id, patient_id, vitals_reading_id, alert_type, severity,
                         title, description, ai_analysis, status, acknowledged_by,
                         acknowledged_at, resolved_by, resolved_at, escalation_level,
                         escalated_at, created_at, updated_at)
                    VALUES
                        (:id, :pid, :vid, :atype, :sev, :title, :desc, :ai, :st,
                         :ack_by, :ack_at, :res_by, :res_at, :esc_lvl, :esc_at,
                         :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "vid": vid,
                    "atype": atype,
                    "sev": sev,
                    "title": f"{atype.replace('_', ' ').title()} Alert",
                    "desc": f"Patient vitals triggered {atype} alert with severity {sev}.",
                    "ai": json.dumps({
                        "recommendation": "Monitor closely" if sev in ("low", "medium") else "Immediate attention required",
                        "confidence": round(random.uniform(0.7, 0.99), 2),
                    }),
                    "st": status,
                    "ack_by": ack_by,
                    "ack_at": ack_at,
                    "res_by": res_by,
                    "res_at": res_at,
                    "esc_lvl": random.randint(0, 3),
                    "esc_at": created + timedelta(minutes=5) if random.random() > 0.5 else None,
                    "ca": created,
                    "ua": res_at or ack_at or created,
                },
            )
        db.session.commit()
        print("  monitoring_alerts: 90 inserted")

        # --- 5. Symptom sessions (90 more) -------------------------------------
        print("Seeding symptom sessions...")
        complaints = [
            "Persistent headache for 3 days",
            "Chest tightness and shortness of breath",
            "Recurring lower back pain",
            "Nausea and vomiting since morning",
            "Fever and chills for 2 days",
            "Dizziness when standing up",
            "Sore throat and difficulty swallowing",
            "Abdominal pain, right side",
            "Numbness in left arm",
            "Chronic fatigue and weakness",
            "Skin rash on arms and neck",
            "Joint pain in both knees",
            "Blurred vision episodes",
            "Heart palpitations at rest",
            "Difficulty sleeping for weeks",
        ]
        triage_levels = ["non_urgent", "semi_urgent", "urgent", "emergency"]
        for i in range(90):
            pid = str(random.choice(patient_user_ids))
            complaint = random.choice(complaints)
            status = random.choice(["in_progress", "completed", "completed", "completed", "cancelled"])
            triage = random.choice(triage_levels) if status == "completed" else None
            created = random_past(90)
            db.session.execute(
                text("""
                    INSERT INTO symptom_sessions
                        (id, patient_id, status, chief_complaint, symptoms,
                         ai_analysis, triage_level, recommended_action,
                         conversation_log, completed_at, created_at, updated_at)
                    VALUES
                        (:id, :pid, :st, :cc, :symp, :ai, :triage, :action,
                         :conv, :comp, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "st": status,
                    "cc": complaint,
                    "symp": json.dumps([
                        {"name": complaint.split()[0], "severity": random.randint(1, 10), "duration_days": random.randint(1, 14)},
                    ]),
                    "ai": json.dumps({
                        "differential_diagnoses": [
                            {"condition": "Common condition A", "confidence": round(random.uniform(0.5, 0.95), 2)},
                            {"condition": "Less likely condition B", "confidence": round(random.uniform(0.1, 0.5), 2)},
                        ],
                        "urgency_score": random.randint(1, 10),
                    }) if status == "completed" else None,
                    "triage": triage,
                    "action": "Schedule follow-up with specialist" if triage in ("semi_urgent", "urgent") else (
                        "Go to emergency room" if triage == "emergency" else "Self-care and monitor"
                    ) if triage else None,
                    "conv": json.dumps([
                        {"role": "patient", "content": complaint, "timestamp": created.isoformat()},
                        {"role": "assistant", "content": "I understand. Can you tell me more about when this started?", "timestamp": (created + timedelta(seconds=5)).isoformat()},
                    ]),
                    "comp": created + timedelta(minutes=random.randint(5, 30)) if status == "completed" else None,
                    "ca": created,
                    "ua": created + timedelta(minutes=random.randint(5, 30)),
                },
            )
        db.session.commit()
        print("  symptom_sessions: 90 inserted")

        # --- 6. Conversations (90 more) ----------------------------------------
        print("Seeding conversations...")
        agent_types = [
            "symptom_analyst", "report_reader", "triage", "voice",
            "drug_interaction", "monitoring", "follow_up", "general",
        ]
        conv_titles = [
            "Headache symptoms discussion",
            "Blood test results review",
            "Medication interaction check",
            "Vital signs anomaly assessment",
            "Follow-up care planning",
            "General health inquiry",
            "Post-surgery recovery check",
            "Diet and exercise guidance",
            "Mental health screening",
            "Chronic pain management",
        ]
        for i in range(90):
            pid = str(random.choice(patient_user_ids))
            agent = random.choice(agent_types)
            created = random_past(90)
            db.session.execute(
                text("""
                    INSERT INTO conversations
                        (id, patient_id, agent_type, title, messages, status,
                         metadata, created_at, updated_at)
                    VALUES
                        (:id, :pid, :agent, :title, :msgs, :st, :meta, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "agent": agent,
                    "title": random.choice(conv_titles),
                    "msgs": json.dumps([
                        {"role": "user", "content": f"I need help with my {random.choice(['headache', 'medication', 'test results', 'vitals', 'care plan'])}.", "timestamp": created.isoformat()},
                        {"role": "assistant", "content": "I am here to help. Could you provide more details?", "timestamp": (created + timedelta(seconds=3)).isoformat()},
                        {"role": "user", "content": "It has been bothering me for a few days.", "timestamp": (created + timedelta(seconds=30)).isoformat()},
                        {"role": "assistant", "content": "Based on the information you provided, here are my recommendations...", "timestamp": (created + timedelta(seconds=35)).isoformat()},
                    ]),
                    "st": random.choice(["active", "closed", "closed", "closed", "escalated"]),
                    "meta": json.dumps({"source": "web", "session_duration_seconds": random.randint(60, 1800)}),
                    "ca": created,
                    "ua": created + timedelta(minutes=random.randint(2, 30)),
                },
            )
        db.session.commit()
        print("  conversations: 90 inserted")

        # --- 7. Notifications (80 more) ----------------------------------------
        print("Seeding notifications...")
        notif_types = [
            "appointment_reminder", "medication_reminder", "vitals_alert",
            "report_ready", "care_plan_update", "message_received",
            "system_notification", "lab_result_available",
        ]
        channels = ["in_app", "email", "sms", "push"]
        for i in range(80):
            uid_val = str(random.choice(all_user_ids))
            ntype = random.choice(notif_types)
            is_read = random.choice([True, False, False])
            created = random_past(60)
            db.session.execute(
                text("""
                    INSERT INTO notifications
                        (id, user_id, type, title, message, data, read, read_at,
                         channel, sent_at, created_at, updated_at)
                    VALUES
                        (:id, :uid, :type, :title, :msg, :data, :read, :read_at,
                         :ch, :sent, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "uid": uid_val,
                    "type": ntype,
                    "title": f"{ntype.replace('_', ' ').title()}",
                    "msg": f"You have a new {ntype.replace('_', ' ')}. Please check your dashboard for details.",
                    "data": json.dumps({"priority": random.choice(["low", "normal", "high"])}),
                    "read": is_read,
                    "read_at": created + timedelta(hours=random.randint(1, 24)) if is_read else None,
                    "ch": random.choice(channels),
                    "sent": created,
                    "ca": created,
                    "ua": created,
                },
            )
        db.session.commit()
        print("  notifications: 80 inserted")

        # --- 8. Lab values (68 more) -------------------------------------------
        print("Seeding lab values...")
        lab_tests = [
            ("Hemoglobin", "g/dL", 12.0, 17.5, "718-7"),
            ("White Blood Cell Count", "10^3/uL", 4.5, 11.0, "6690-2"),
            ("Platelet Count", "10^3/uL", 150.0, 400.0, "777-3"),
            ("Glucose", "mg/dL", 70.0, 100.0, "2345-7"),
            ("Creatinine", "mg/dL", 0.6, 1.2, "2160-0"),
            ("BUN", "mg/dL", 7.0, 20.0, "3094-0"),
            ("Sodium", "mEq/L", 136.0, 145.0, "2951-2"),
            ("Potassium", "mEq/L", 3.5, 5.0, "2823-3"),
            ("Calcium", "mg/dL", 8.5, 10.5, "17861-6"),
            ("Total Cholesterol", "mg/dL", 0.0, 200.0, "2093-3"),
            ("HDL Cholesterol", "mg/dL", 40.0, 60.0, "2085-9"),
            ("LDL Cholesterol", "mg/dL", 0.0, 100.0, "2089-1"),
            ("Triglycerides", "mg/dL", 0.0, 150.0, "2571-8"),
            ("TSH", "mIU/L", 0.4, 4.0, "3016-3"),
            ("HbA1c", "%", 4.0, 5.6, "4548-4"),
            ("ALT", "U/L", 7.0, 56.0, "1742-6"),
            ("AST", "U/L", 10.0, 40.0, "1920-8"),
        ]
        for i in range(68):
            test = random.choice(lab_tests)
            report = random.choice(report_rows)
            # Sometimes generate abnormal values
            if random.random() < 0.25:
                val = round(test[3] + random.uniform(1, test[3] * 0.3), 1)
                abnormal = True
            elif random.random() < 0.15:
                val = round(max(0, test[2] - random.uniform(1, test[2] * 0.3)), 1)
                abnormal = True
            else:
                val = round(random.uniform(test[2], test[3]), 1)
                abnormal = False
            db.session.execute(
                text("""
                    INSERT INTO lab_values
                        (id, report_id, patient_id, test_name, value, unit,
                         reference_min, reference_max, is_abnormal, loinc_code,
                         collected_at, created_at, updated_at)
                    VALUES
                        (:id, :rid, :pid, :name, :val, :unit, :rmin, :rmax,
                         :abn, :loinc, :coll, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "rid": str(report[0]),
                    "pid": str(report[1]),
                    "name": test[0],
                    "val": val,
                    "unit": test[1],
                    "rmin": test[2],
                    "rmax": test[3],
                    "abn": abnormal,
                    "loinc": test[4],
                    "coll": random_past(90),
                    "ca": random_past(90),
                    "ua": random_past(30),
                },
            )
        db.session.commit()
        print("  lab_values: 68 inserted")

        # --- 9. Allergies (76 more) --------------------------------------------
        print("Seeding allergies...")
        allergens = [
            "Penicillin", "Amoxicillin", "Sulfa drugs", "Aspirin", "Ibuprofen",
            "Codeine", "Morphine", "Latex", "Shellfish", "Peanuts",
            "Tree nuts", "Eggs", "Milk", "Soy", "Wheat", "Bee stings",
            "Dust mites", "Pollen", "Cat dander", "Dog dander",
            "Mold", "Nickel", "Contrast dye", "Lidocaine", "Tetracycline",
        ]
        reactions = [
            "Hives and skin rash", "Anaphylaxis", "Swelling of face/throat",
            "Difficulty breathing", "Nausea and vomiting", "Itching",
            "Stomach cramps", "Dizziness", "Runny nose and sneezing",
        ]
        sev_options = ["mild", "moderate", "severe", "life_threatening"]
        for i in range(76):
            pid = str(random.choice(patient_user_ids))
            db.session.execute(
                text("""
                    INSERT INTO allergies
                        (id, patient_id, allergen, reaction, severity,
                         diagnosed_date, created_by, created_at, updated_at)
                    VALUES
                        (:id, :pid, :allergen, :reaction, :sev, :dd, :cb, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "allergen": random.choice(allergens),
                    "reaction": random.choice(reactions),
                    "sev": random.choice(sev_options),
                    "dd": date.today() - timedelta(days=random.randint(365, 3650)),
                    "cb": pid,
                    "ca": random_past(365),
                    "ua": random_past(60),
                },
            )
        db.session.commit()
        print("  allergies: 76 inserted")

        # --- 10. Care plans (85 more) ------------------------------------------
        print("Seeding care plans...")
        care_plan_titles = [
            "Diabetes Management Plan", "Hypertension Control Program",
            "Post-Surgery Recovery Plan", "Weight Management Program",
            "Cardiac Rehabilitation Plan", "Asthma Management Plan",
            "Chronic Pain Management", "Mental Health Support Plan",
            "Prenatal Care Plan", "Oncology Follow-Up Plan",
            "Renal Health Management", "COPD Management Plan",
            "Osteoporosis Prevention Plan", "Stroke Recovery Plan",
        ]
        cp_statuses = ["draft", "active", "active", "active", "completed", "cancelled"]
        for i in range(85):
            pid = str(random.choice(patient_user_ids))
            did = str(random.choice(doctor_user_ids))
            status = random.choice(cp_statuses)
            start = date.today() - timedelta(days=random.randint(1, 180))
            end = start + timedelta(days=random.randint(30, 365))
            db.session.execute(
                text("""
                    INSERT INTO care_plans
                        (id, patient_id, doctor_id, title, description, status,
                         start_date, end_date, ai_recommendations, created_by,
                         created_at, updated_at)
                    VALUES
                        (:id, :pid, :did, :title, :desc, :st, :sd, :ed,
                         :ai, :cb, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "did": did,
                    "title": random.choice(care_plan_titles),
                    "desc": f"Comprehensive care plan for patient. Includes medication schedule, lifestyle modifications, and follow-up appointments.",
                    "st": status,
                    "sd": start,
                    "ed": end,
                    "ai": json.dumps({
                        "lifestyle": ["Regular exercise 30 min/day", "Low sodium diet", "Adequate sleep 7-8 hours"],
                        "monitoring": ["Weekly blood pressure check", "Monthly lab work"],
                    }),
                    "cb": did,
                    "ca": random_past(180),
                    "ua": random_past(30),
                },
            )
        db.session.commit()
        print("  care_plans: 85 inserted")

        # --- 11. Medications (80 more) -----------------------------------------
        print("Seeding medications...")
        meds = [
            ("Metformin", "500mg", "Twice daily", "oral", "Blood sugar control"),
            ("Lisinopril", "10mg", "Once daily", "oral", "Blood pressure management"),
            ("Atorvastatin", "20mg", "Once daily at bedtime", "oral", "Cholesterol management"),
            ("Amlodipine", "5mg", "Once daily", "oral", "Blood pressure management"),
            ("Metoprolol", "25mg", "Twice daily", "oral", "Heart rate control"),
            ("Omeprazole", "20mg", "Once daily before breakfast", "oral", "Acid reflux"),
            ("Levothyroxine", "50mcg", "Once daily on empty stomach", "oral", "Thyroid replacement"),
            ("Sertraline", "50mg", "Once daily", "oral", "Depression/anxiety"),
            ("Albuterol", "2 puffs", "Every 4-6 hours as needed", "inhalation", "Asthma/COPD"),
            ("Gabapentin", "300mg", "Three times daily", "oral", "Neuropathic pain"),
            ("Prednisone", "10mg", "Once daily", "oral", "Inflammation"),
            ("Warfarin", "5mg", "Once daily", "oral", "Blood clot prevention"),
            ("Insulin Glargine", "20 units", "Once daily at bedtime", "subcutaneous", "Diabetes"),
            ("Losartan", "50mg", "Once daily", "oral", "Blood pressure management"),
            ("Hydrochlorothiazide", "25mg", "Once daily", "oral", "Blood pressure/edema"),
        ]
        med_statuses = ["active", "active", "active", "completed", "discontinued", "on_hold"]
        for i in range(80):
            med = random.choice(meds)
            pid = str(random.choice(patient_user_ids))
            did = str(random.choice(doctor_user_ids))
            status = random.choice(med_statuses)
            start = date.today() - timedelta(days=random.randint(1, 365))
            end = start + timedelta(days=random.randint(30, 365)) if status in ("completed", "discontinued") else None
            db.session.execute(
                text("""
                    INSERT INTO medications
                        (id, patient_id, name, dosage, frequency, route,
                         prescribed_by, start_date, end_date, status, reason,
                         side_effects, refills_remaining, pharmacy_notes,
                         created_by, created_at, updated_at)
                    VALUES
                        (:id, :pid, :name, :dos, :freq, :route, :presc,
                         :sd, :ed, :st, :reason, :se, :refills, :pnotes,
                         :cb, :ca, :ua)
                """),
                {
                    "id": uid(),
                    "pid": pid,
                    "name": med[0],
                    "dos": med[1],
                    "freq": med[2],
                    "route": med[3],
                    "presc": did,
                    "sd": start,
                    "ed": end,
                    "st": status,
                    "reason": med[4],
                    "se": random.choice([None, "Mild nausea", "Dizziness", "Headache", "Fatigue"]),
                    "refills": random.randint(0, 5),
                    "pnotes": None,
                    "cb": did,
                    "ca": random_past(365),
                    "ua": random_past(30),
                },
            )
        db.session.commit()
        print("  medications: 80 inserted")

        # --- Final counts -------------------------------------------------------
        print("\n=== Final table counts ===")
        result = db.session.execute(text("""
            SELECT table_name, (xpath('/row/cnt/text()', xml_count))[1]::text::int AS row_count
            FROM (
                SELECT table_name, query_to_xml(format('SELECT count(*) AS cnt FROM %I.%I', table_schema, table_name), false, true, '') AS xml_count
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ) t ORDER BY row_count DESC
        """))
        for row in result:
            marker = " <-- BELOW 100" if row[1] < 100 else ""
            print(f"  {row[0]}: {row[1]}{marker}")


if __name__ == "__main__":
    seed()
