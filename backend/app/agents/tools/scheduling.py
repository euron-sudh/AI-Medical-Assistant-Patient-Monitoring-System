"""Scheduling & Care Plan Tool — generates care plans and manages follow-ups.

Provides tools for the FollowUpAgent to generate personalized care plans,
track patient adherence to medications and appointments, and schedule
follow-up visits.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import uuid

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Care plan templates by diagnosis category
# ---------------------------------------------------------------------------

CARE_PLAN_TEMPLATES: dict[str, dict] = {
    "hypertension": {
        "condition": "Hypertension",
        "lifestyle_modifications": [
            "Reduce sodium intake to less than 2,300 mg/day",
            "Engage in 150 minutes of moderate aerobic exercise per week",
            "Maintain healthy weight (BMI 18.5-24.9)",
            "Limit alcohol to 1-2 drinks per day",
            "Follow DASH diet (fruits, vegetables, whole grains, low-fat dairy)",
            "Monitor blood pressure at home twice daily",
        ],
        "monitoring": [
            "Daily blood pressure readings (morning and evening)",
            "Weekly weight check",
            "Monthly review of BP log with provider",
        ],
        "follow_up_interval_days": 30,
        "red_flags": [
            "BP > 180/120 mmHg",
            "Severe headache with vision changes",
            "Chest pain or shortness of breath",
        ],
    },
    "diabetes_type2": {
        "condition": "Type 2 Diabetes Mellitus",
        "lifestyle_modifications": [
            "Follow consistent carbohydrate meal plan",
            "Exercise 150 minutes/week (moderate intensity)",
            "Monitor blood glucose as directed",
            "Annual eye examination",
            "Daily foot inspection",
            "Maintain HbA1c below 7%",
        ],
        "monitoring": [
            "Blood glucose monitoring per provider schedule",
            "HbA1c every 3 months",
            "Annual comprehensive metabolic panel",
            "Annual microalbumin/creatinine ratio",
        ],
        "follow_up_interval_days": 90,
        "red_flags": [
            "Blood glucose > 300 mg/dL or < 54 mg/dL",
            "Signs of DKA: nausea, vomiting, fruity breath",
            "Non-healing foot wound",
        ],
    },
    "asthma": {
        "condition": "Asthma",
        "lifestyle_modifications": [
            "Identify and avoid triggers",
            "Use inhaler technique correctly",
            "Keep rescue inhaler accessible at all times",
            "Annual flu vaccination",
            "Maintain asthma action plan",
        ],
        "monitoring": [
            "Peak flow readings as directed",
            "Track rescue inhaler usage",
            "Review asthma control questionnaire monthly",
        ],
        "follow_up_interval_days": 90,
        "red_flags": [
            "Using rescue inhaler > 2 times per week",
            "Waking at night due to asthma symptoms",
            "Difficulty speaking in full sentences",
        ],
    },
    "general": {
        "condition": "General Follow-Up",
        "lifestyle_modifications": [
            "Maintain balanced diet rich in fruits and vegetables",
            "Exercise at least 150 minutes per week",
            "Get 7-9 hours of sleep per night",
            "Stay hydrated (8 glasses of water daily)",
            "Manage stress through relaxation techniques",
        ],
        "monitoring": [
            "Annual physical examination",
            "Age-appropriate preventive screenings",
            "Track any new or worsening symptoms",
        ],
        "follow_up_interval_days": 365,
        "red_flags": [
            "Unexplained weight loss > 10% in 6 months",
            "Persistent fever > 3 days",
            "New or worsening symptoms",
        ],
    },
}


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

GENERATE_CARE_PLAN_TOOL = {
    "type": "function",
    "function": {
        "name": "generate_care_plan",
        "description": (
            "Generate a personalized care plan based on the patient's diagnosis "
            "and profile. Includes lifestyle modifications, monitoring schedule, "
            "follow-up intervals, and red flags to watch for."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "diagnosis": {
                    "type": "string",
                    "description": "Primary diagnosis or condition (e.g. hypertension, diabetes_type2)",
                },
                "patient_profile": {
                    "type": "object",
                    "description": (
                        "Patient profile including age, conditions, medications, and preferences. "
                        "Keys may include: age, gender, conditions, medications, allergies"
                    ),
                },
            },
            "required": ["diagnosis", "patient_profile"],
        },
    },
}

TRACK_ADHERENCE_TOOL = {
    "type": "function",
    "function": {
        "name": "track_adherence",
        "description": (
            "Check a patient's adherence to their prescribed medications and "
            "scheduled appointments. Returns adherence score and any missed items."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient UUID",
                },
            },
            "required": ["patient_id"],
        },
    },
}

SCHEDULE_FOLLOW_UP_TOOL = {
    "type": "function",
    "function": {
        "name": "schedule_follow_up",
        "description": (
            "Schedule a follow-up appointment for a patient. Specifies the number "
            "of days from now and the reason for the visit."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient UUID",
                },
                "days_from_now": {
                    "type": "integer",
                    "description": "Number of days from today to schedule the follow-up",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the follow-up appointment",
                },
            },
            "required": ["patient_id", "days_from_now", "reason"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool handler functions
# ---------------------------------------------------------------------------


def generate_care_plan(diagnosis: str, patient_profile: dict) -> dict:
    """Generate a personalized care plan based on diagnosis and patient profile.

    Args:
        diagnosis: Primary diagnosis or condition key.
        patient_profile: Patient demographics, conditions, medications, etc.

    Returns:
        Personalized care plan dict.
    """
    key = diagnosis.strip().lower().replace(" ", "_")
    template = CARE_PLAN_TEMPLATES.get(key, CARE_PLAN_TEMPLATES["general"])

    # Personalize based on patient profile
    age = patient_profile.get("age", 0)
    conditions = patient_profile.get("conditions", [])
    medications = patient_profile.get("medications", [])

    care_plan = {
        "plan_id": str(uuid.uuid4()),
        "condition": template["condition"],
        "created_date": datetime.utcnow().isoformat(),
        "patient_profile_summary": {
            "age": age,
            "existing_conditions": conditions,
            "current_medications": medications,
        },
        "lifestyle_modifications": list(template["lifestyle_modifications"]),
        "monitoring_schedule": list(template["monitoring"]),
        "follow_up_interval_days": template["follow_up_interval_days"],
        "next_follow_up": (
            datetime.utcnow() + timedelta(days=template["follow_up_interval_days"])
        ).strftime("%Y-%m-%d"),
        "red_flags": template["red_flags"],
    }

    # Age-specific adjustments
    if age >= 65:
        care_plan["lifestyle_modifications"].append(
            "Fall prevention: ensure adequate lighting and remove tripping hazards"
        )
        care_plan["monitoring_schedule"].append(
            "Annual cognitive screening recommended for patients 65+"
        )
    if age < 18:
        care_plan["lifestyle_modifications"].append(
            "Ensure age-appropriate physical activity and nutrition for growth"
        )

    # Multi-morbidity considerations
    if len(conditions) > 2:
        care_plan["notes"] = (
            "Multiple comorbidities detected. Coordinate care across specialists "
            "and review for polypharmacy risks."
        )

    logger.info(
        "care_plan_generated",
        diagnosis=key,
        patient_age=age,
        condition_count=len(conditions),
    )

    return care_plan


def track_adherence(patient_id: str) -> dict:
    """Check medication and appointment adherence for a patient.

    Note: In production, this queries the patient's medication log and
    appointment history from the database. This implementation returns
    a placeholder indicating the infrastructure is ready.

    Args:
        patient_id: Patient UUID.

    Returns:
        Adherence tracking summary dict.
    """
    logger.info("adherence_check_requested", patient_id=patient_id)

    # Placeholder: in production, fetch real data from patient records
    return {
        "patient_id": patient_id,
        "check_date": datetime.utcnow().isoformat(),
        "medication_adherence": {
            "score": None,
            "status": "pending_data",
            "message": (
                "Medication adherence tracking requires connection to the patient's "
                "medication log. Connect to the pharmacy/EHR system for real-time data."
            ),
        },
        "appointment_adherence": {
            "upcoming_appointments": [],
            "missed_appointments": [],
            "status": "pending_data",
            "message": (
                "Appointment tracking requires connection to the scheduling system. "
                "Integration pending."
            ),
        },
        "overall_message": (
            "Adherence tracking infrastructure is ready. Connect patient data "
            "sources for personalized adherence monitoring."
        ),
    }


def schedule_follow_up(
    patient_id: str,
    days_from_now: int,
    reason: str,
) -> dict:
    """Schedule a follow-up appointment for a patient.

    Note: In production, this creates an appointment in the scheduling system.
    This implementation returns a confirmation placeholder.

    Args:
        patient_id: Patient UUID.
        days_from_now: Number of days from today.
        reason: Reason for the follow-up.

    Returns:
        Appointment confirmation dict.
    """
    scheduled_date = (datetime.utcnow() + timedelta(days=days_from_now)).strftime("%Y-%m-%d")
    appointment_id = str(uuid.uuid4())

    logger.info(
        "follow_up_scheduled",
        patient_id=patient_id,
        scheduled_date=scheduled_date,
        reason=reason,
        appointment_id=appointment_id,
    )

    return {
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "scheduled_date": scheduled_date,
        "days_from_now": days_from_now,
        "reason": reason,
        "status": "scheduled",
        "message": (
            f"Follow-up appointment scheduled for {scheduled_date} "
            f"({days_from_now} days from now). Reason: {reason}. "
            "Patient will receive a reminder notification."
        ),
    }
