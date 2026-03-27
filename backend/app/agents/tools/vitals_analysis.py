"""Vitals Analysis Tool — analyze patient vitals and compute early warning scores.

Provides tools for the MonitoringAgent to compare vitals against normal ranges,
detect anomalies, compute the NEWS2 (National Early Warning Score 2), and
detect worsening trends over time.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Vital sign reference ranges: normal / warning / critical thresholds
# ---------------------------------------------------------------------------

VITAL_RANGES: dict[str, dict] = {
    "heart_rate": {
        "unit": "bpm",
        "normal_min": 60,
        "normal_max": 100,
        "warning_low": 50,
        "warning_high": 110,
        "critical_low": 40,
        "critical_high": 130,
    },
    "bp_systolic": {
        "unit": "mmHg",
        "normal_min": 90,
        "normal_max": 140,
        "warning_low": 80,
        "warning_high": 160,
        "critical_low": 70,
        "critical_high": 180,
    },
    "bp_diastolic": {
        "unit": "mmHg",
        "normal_min": 60,
        "normal_max": 90,
        "warning_low": 50,
        "warning_high": 100,
        "critical_low": 40,
        "critical_high": 110,
    },
    "temperature": {
        "unit": "C",
        "normal_min": 36.1,
        "normal_max": 37.2,
        "warning_low": 35.5,
        "warning_high": 38.0,
        "critical_low": 35.0,
        "critical_high": 39.0,
    },
    "respiratory_rate": {
        "unit": "breaths/min",
        "normal_min": 12,
        "normal_max": 20,
        "warning_low": 9,
        "warning_high": 24,
        "critical_low": 8,
        "critical_high": 30,
    },
    "spo2": {
        "unit": "%",
        "normal_min": 95,
        "normal_max": 100,
        "warning_low": 92,
        "warning_high": 100,
        "critical_low": 88,
        "critical_high": 100,
    },
    "blood_glucose": {
        "unit": "mg/dL",
        "normal_min": 70,
        "normal_max": 140,
        "warning_low": 54,
        "warning_high": 200,
        "critical_low": 40,
        "critical_high": 400,
    },
}


# ---------------------------------------------------------------------------
# NEWS2 scoring tables (Royal College of Physicians)
# ---------------------------------------------------------------------------

NEWS2_RESPIRATION_RATE = [
    (8, 3), (9, 1), (12, 0), (20, 0), (24, 2), (float("inf"), 3),
]

NEWS2_SPO2_SCALE1 = [
    (91, 3), (93, 2), (95, 1), (float("inf"), 0),
]

NEWS2_SYSTOLIC_BP = [
    (90, 3), (100, 2), (110, 1), (219, 0), (float("inf"), 3),
]

NEWS2_HEART_RATE = [
    (40, 3), (50, 1), (90, 0), (110, 1), (130, 2), (float("inf"), 3),
]

NEWS2_TEMPERATURE = [
    (35.0, 3), (36.0, 1), (38.0, 0), (39.0, 1), (float("inf"), 2),
]


def _score_from_table(value: float, table: list[tuple[float, int]]) -> int:
    """Look up a NEWS2 sub-score from a threshold table."""
    for threshold, score in table:
        if value <= threshold:
            return score
    return table[-1][1]


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

ANALYZE_VITALS_TOOL = {
    "type": "function",
    "function": {
        "name": "analyze_vitals",
        "description": (
            "Analyze a set of vital signs by comparing against normal, warning, and critical "
            "thresholds. Returns the status of each vital and any detected anomalies."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "vitals_dict": {
                    "type": "object",
                    "description": (
                        "Dict mapping vital sign names to numeric values. "
                        "Keys: heart_rate, bp_systolic, bp_diastolic, temperature, "
                        "respiratory_rate, spo2, blood_glucose"
                    ),
                },
            },
            "required": ["vitals_dict"],
        },
    },
}

CALCULATE_NEWS2_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_news2",
        "description": (
            "Compute the NEWS2 (National Early Warning Score 2) from vital signs. "
            "Returns the total score and clinical risk level (low/low-medium/medium/high)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "hr": {"type": "number", "description": "Heart rate in bpm"},
                "bp_sys": {"type": "number", "description": "Systolic blood pressure in mmHg"},
                "bp_dia": {"type": "number", "description": "Diastolic blood pressure in mmHg"},
                "temp": {"type": "number", "description": "Body temperature in C"},
                "rr": {"type": "number", "description": "Respiratory rate in breaths/min"},
                "spo2": {"type": "number", "description": "Oxygen saturation percentage"},
            },
            "required": ["hr", "bp_sys", "bp_dia", "temp", "rr", "spo2"],
        },
    },
}

DETECT_TREND_TOOL = {
    "type": "function",
    "function": {
        "name": "detect_trend",
        "description": (
            "Detect worsening or improving trends in a patient's vital signs "
            "over a given time window. Returns trend direction and alerts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "Patient UUID",
                },
                "vital_type": {
                    "type": "string",
                    "description": "Type of vital sign to analyze (e.g. heart_rate, bp_systolic)",
                },
                "hours": {
                    "type": "integer",
                    "description": "Number of hours to look back (default 24)",
                    "default": 24,
                },
            },
            "required": ["patient_id", "vital_type"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool handler functions
# ---------------------------------------------------------------------------


def analyze_vitals(vitals_dict: dict[str, float]) -> dict:
    """Analyze vital signs against normal/warning/critical thresholds.

    Args:
        vitals_dict: Dict mapping vital sign name to numeric value.

    Returns:
        Analysis dict with status per vital and overall assessment.
    """
    results = {}
    anomalies = []
    overall_status = "normal"

    for vital_name, value in vitals_dict.items():
        ref = VITAL_RANGES.get(vital_name)
        if not ref:
            results[vital_name] = {
                "value": value,
                "status": "unknown",
                "message": f"No reference range available for '{vital_name}'",
            }
            continue

        # Determine status
        if ref["normal_min"] <= value <= ref["normal_max"]:
            status = "normal"
            message = f"{vital_name} is within normal range"
        elif value <= ref["critical_low"] or value >= ref["critical_high"]:
            status = "critical"
            message = f"{vital_name} is critically {'low' if value < ref['normal_min'] else 'high'}"
            anomalies.append({"vital": vital_name, "value": value, "status": status, "message": message})
            overall_status = "critical"
        elif value <= ref["warning_low"] or value >= ref["warning_high"]:
            status = "warning"
            message = f"{vital_name} is {'below' if value < ref['normal_min'] else 'above'} normal range"
            anomalies.append({"vital": vital_name, "value": value, "status": status, "message": message})
            if overall_status != "critical":
                overall_status = "warning"
        else:
            # Between warning and normal thresholds — mildly abnormal
            status = "mildly_abnormal"
            message = f"{vital_name} is slightly {'low' if value < ref['normal_min'] else 'high'}"
            anomalies.append({"vital": vital_name, "value": value, "status": status, "message": message})
            if overall_status == "normal":
                overall_status = "mildly_abnormal"

        results[vital_name] = {
            "value": value,
            "unit": ref["unit"],
            "status": status,
            "normal_range": f"{ref['normal_min']}-{ref['normal_max']}",
            "message": message,
        }

    logger.info(
        "vitals_analyzed",
        vitals_count=len(vitals_dict),
        anomaly_count=len(anomalies),
        overall_status=overall_status,
    )

    return {
        "vitals": results,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "overall_status": overall_status,
        "requires_attention": overall_status in ("critical", "warning"),
    }


def calculate_news2(
    hr: float,
    bp_sys: float,
    bp_dia: float,
    temp: float,
    rr: float,
    spo2: float,
) -> dict:
    """Compute NEWS2 score from vital signs.

    Args:
        hr: Heart rate (bpm).
        bp_sys: Systolic blood pressure (mmHg).
        bp_dia: Diastolic blood pressure (mmHg) — used for context, not in NEWS2 directly.
        temp: Body temperature (C).
        rr: Respiratory rate (breaths/min).
        spo2: Oxygen saturation (%).

    Returns:
        Dict with total score, sub-scores, risk level, and clinical response.
    """
    sub_scores = {
        "respiration_rate": _score_from_table(rr, NEWS2_RESPIRATION_RATE),
        "spo2": _score_from_table(spo2, NEWS2_SPO2_SCALE1),
        "systolic_bp": _score_from_table(bp_sys, NEWS2_SYSTOLIC_BP),
        "heart_rate": _score_from_table(hr, NEWS2_HEART_RATE),
        "temperature": _score_from_table(temp, NEWS2_TEMPERATURE),
    }

    # Consciousness: assume Alert (score 0) — would need AVPU input for full assessment
    sub_scores["consciousness"] = 0

    total_score = sum(sub_scores.values())

    # Determine clinical risk and recommended response
    # Check for any single parameter scoring 3
    any_single_extreme = any(v == 3 for v in sub_scores.values())

    if total_score >= 7:
        risk_level = "high"
        clinical_response = (
            "Emergency response — continuous monitoring, urgent clinical review by "
            "critical care team, consider transfer to ICU"
        )
    elif total_score >= 5 or any_single_extreme:
        risk_level = "medium"
        clinical_response = (
            "Urgent response — increased monitoring frequency, urgent clinical review "
            "within 30 minutes, consider critical care referral"
        )
    elif total_score >= 1:
        risk_level = "low-medium"
        clinical_response = (
            "Low-medium risk — increase monitoring to minimum 4-hourly, "
            "inform registered nurse, assess by competent clinical decision-maker"
        )
    else:
        risk_level = "low"
        clinical_response = "Low risk — continue routine monitoring every 12 hours minimum"

    logger.info(
        "news2_calculated",
        total_score=total_score,
        risk_level=risk_level,
    )

    return {
        "total_score": total_score,
        "sub_scores": sub_scores,
        "risk_level": risk_level,
        "clinical_response": clinical_response,
        "vitals_used": {
            "heart_rate": hr,
            "bp_systolic": bp_sys,
            "bp_diastolic": bp_dia,
            "temperature": temp,
            "respiratory_rate": rr,
            "spo2": spo2,
        },
    }


def detect_trend(
    patient_id: str,
    vital_type: str,
    hours: int = 24,
) -> dict:
    """Detect worsening or improving trends in a patient's vitals.

    Note: In production, this would query a time-series database for historical
    vital sign readings. This implementation returns a placeholder analysis
    indicating the infrastructure is ready for real-time data integration.

    Args:
        patient_id: Patient UUID.
        vital_type: Type of vital to analyze.
        hours: Hours of history to review.

    Returns:
        Trend analysis dict with direction and alerts.
    """
    ref = VITAL_RANGES.get(vital_type)

    logger.info(
        "trend_detection_requested",
        patient_id=patient_id,
        vital_type=vital_type,
        hours=hours,
    )

    if not ref:
        return {
            "patient_id": patient_id,
            "vital_type": vital_type,
            "status": "error",
            "message": f"Unknown vital type: {vital_type}",
        }

    # Placeholder: in production, fetch real data from the vitals time-series store
    return {
        "patient_id": patient_id,
        "vital_type": vital_type,
        "time_window_hours": hours,
        "trend_direction": "stable",
        "trend_description": (
            f"Trend analysis for {vital_type} over the last {hours} hours. "
            "Requires historical vital sign data from the monitoring system. "
            "Connect to the patient vitals database for real-time trend analysis."
        ),
        "normal_range": f"{ref['normal_min']}-{ref['normal_max']} {ref['unit']}",
        "data_points_available": 0,
        "alert_level": "none",
        "message": "Historical data integration pending — connect vitals monitoring feed",
    }
