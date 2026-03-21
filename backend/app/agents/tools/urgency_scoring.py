"""Urgency scoring tool — compute urgency scores and recommend actions.

Provides rule-based urgency scoring for symptom analysis. Considers symptom
severity, duration, red-flag patterns, and patient risk factors to produce
a 1-10 urgency score and recommended action.
"""

import structlog

logger = structlog.get_logger(__name__)


# Red-flag symptoms that always elevate urgency
RED_FLAG_SYMPTOMS = {
    "chest pain": 9,
    "difficulty breathing": 9,
    "shortness of breath": 9,
    "severe headache": 7,
    "thunderclap headache": 10,
    "loss of consciousness": 9,
    "seizure": 9,
    "stroke symptoms": 10,
    "facial drooping": 10,
    "arm weakness": 8,
    "speech difficulty": 9,
    "slurred speech": 9,
    "severe bleeding": 9,
    "suicidal thoughts": 10,
    "self harm": 10,
    "allergic reaction": 8,
    "anaphylaxis": 10,
    "high fever": 7,
    "stiff neck with fever": 9,
    "vision loss": 8,
    "sudden vision change": 8,
}


# OpenAI function-calling tool definition
CALCULATE_URGENCY_SCORE_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_urgency_score",
        "description": (
            "Calculate an urgency score (1-10) for the reported symptoms. "
            "The score considers symptom severity, duration, red-flag patterns, "
            "and patient risk factors. Use this after gathering sufficient symptom "
            "information to determine the appropriate level of care."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of reported symptoms",
                },
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe"],
                    "description": "Patient-reported overall severity",
                },
                "duration_hours": {
                    "type": "number",
                    "description": "How long symptoms have been present, in hours",
                },
                "patient_age": {
                    "type": "integer",
                    "description": "Patient's age in years (affects risk assessment)",
                },
            },
            "required": ["symptoms", "severity"],
        },
    },
}

RECOMMEND_SPECIALIST_TOOL = {
    "type": "function",
    "function": {
        "name": "recommend_specialist",
        "description": (
            "Recommend a medical specialist type based on the symptom profile "
            "and differential diagnosis. Maps symptoms and conditions to the "
            "appropriate specialist for referral."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "primary_symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The main symptoms driving the referral",
                },
                "suspected_conditions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suspected diagnoses from differential",
                },
            },
            "required": ["primary_symptoms"],
        },
    },
}


# Specialist mapping by symptom/condition keywords
SPECIALIST_MAP = {
    "heart": "Cardiology",
    "chest pain": "Cardiology",
    "cardiac": "Cardiology",
    "breathing": "Pulmonology",
    "lung": "Pulmonology",
    "cough": "Pulmonology",
    "headache": "Neurology",
    "seizure": "Neurology",
    "numbness": "Neurology",
    "skin": "Dermatology",
    "rash": "Dermatology",
    "joint": "Rheumatology",
    "bone": "Orthopedics",
    "stomach": "Gastroenterology",
    "digestive": "Gastroenterology",
    "nausea": "Gastroenterology",
    "eye": "Ophthalmology",
    "vision": "Ophthalmology",
    "ear": "ENT (Otolaryngology)",
    "throat": "ENT (Otolaryngology)",
    "mental health": "Psychiatry",
    "anxiety": "Psychiatry",
    "depression": "Psychiatry",
    "diabetes": "Endocrinology",
    "thyroid": "Endocrinology",
    "kidney": "Nephrology",
    "urinary": "Urology",
}


def calculate_urgency_score(
    symptoms: list[str],
    severity: str,
    duration_hours: float | None = None,
    patient_age: int | None = None,
) -> dict:
    """Calculate an urgency score for the reported symptoms.

    Uses a rule-based approach combining red-flag pattern matching,
    patient-reported severity, symptom duration, and age-based risk factors.

    Args:
        symptoms: List of reported symptom strings.
        severity: Patient-reported severity (mild, moderate, severe).
        duration_hours: How long symptoms have been present.
        patient_age: Patient age for risk adjustment.

    Returns:
        Dict with urgency_score (1-10), red_flags found, and recommended_action.
    """
    logger.info(
        "calculate_urgency_score",
        symptom_count=len(symptoms),
        severity=severity,
    )

    # Base score from severity
    severity_scores = {"mild": 2, "moderate": 5, "severe": 7}
    base_score = severity_scores.get(severity, 5)

    # Check for red-flag symptoms
    detected_red_flags: list[str] = []
    max_red_flag_score = 0

    for symptom in symptoms:
        symptom_lower = symptom.lower().strip()
        for red_flag, flag_score in RED_FLAG_SYMPTOMS.items():
            if red_flag in symptom_lower:
                detected_red_flags.append(red_flag)
                max_red_flag_score = max(max_red_flag_score, flag_score)

    # Use the higher of base score and red-flag score
    urgency_score = max(base_score, max_red_flag_score)

    # Age adjustment: higher risk for very young (<5) and elderly (>65)
    if patient_age is not None:
        if patient_age < 5 or patient_age > 65:
            urgency_score = min(10, urgency_score + 1)

    # Duration adjustment: acute onset is generally more concerning
    if duration_hours is not None and duration_hours < 1:
        urgency_score = min(10, urgency_score + 1)

    urgency_score = max(1, min(10, urgency_score))

    # Determine recommended action
    if urgency_score >= 9:
        recommended_action = "Call emergency services (911) immediately"
    elif urgency_score >= 7:
        recommended_action = "Seek emergency care or urgent care within 1 hour"
    elif urgency_score >= 5:
        recommended_action = "Schedule an appointment with your doctor within 24 hours"
    elif urgency_score >= 3:
        recommended_action = "Schedule a routine appointment with your doctor"
    else:
        recommended_action = "Monitor symptoms at home; seek care if they worsen"

    return {
        "urgency_score": urgency_score,
        "severity_input": severity,
        "red_flags_detected": detected_red_flags,
        "recommended_action": recommended_action,
        "factors": {
            "base_severity_score": base_score,
            "red_flag_score": max_red_flag_score,
            "age_adjusted": patient_age is not None and (patient_age < 5 or patient_age > 65),
            "acute_onset": duration_hours is not None and duration_hours < 1,
        },
    }


def recommend_specialist(
    primary_symptoms: list[str],
    suspected_conditions: list[str] | None = None,
) -> dict:
    """Recommend a specialist based on symptoms and suspected conditions.

    Args:
        primary_symptoms: Main symptoms driving the referral.
        suspected_conditions: Suspected diagnoses, if available.

    Returns:
        Dict with recommended_specialist and reasoning.
    """
    logger.info(
        "recommend_specialist",
        symptom_count=len(primary_symptoms),
        condition_count=len(suspected_conditions) if suspected_conditions else 0,
    )

    # Combine symptoms and conditions for keyword matching
    all_terms = [s.lower() for s in primary_symptoms]
    if suspected_conditions:
        all_terms.extend(c.lower() for c in suspected_conditions)

    # Find matching specialists
    matches: dict[str, int] = {}
    for term in all_terms:
        for keyword, specialist in SPECIALIST_MAP.items():
            if keyword in term:
                matches[specialist] = matches.get(specialist, 0) + 1

    if not matches:
        return {
            "recommended_specialist": "General Practice / Internal Medicine",
            "reasoning": "No specific specialist match found; recommend general practitioner for initial evaluation.",
            "alternative_specialists": [],
        }

    # Sort by match count (most relevant specialist first)
    sorted_specialists = sorted(matches.items(), key=lambda x: x[1], reverse=True)
    primary_specialist = sorted_specialists[0][0]
    alternatives = [s[0] for s in sorted_specialists[1:3]]

    return {
        "recommended_specialist": primary_specialist,
        "reasoning": f"Based on symptoms: {', '.join(primary_symptoms[:3])}",
        "alternative_specialists": alternatives,
    }
