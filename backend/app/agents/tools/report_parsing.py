"""Report Parsing Tool — extracts structured data from medical reports.

Provides tools for the ReportReaderAgent to parse lab values,
identify abnormalities, and generate summaries.
"""

from __future__ import annotations

# Reference ranges for common lab tests
REFERENCE_RANGES: dict[str, dict] = {
    "hemoglobin": {"unit": "g/dL", "min": 12.0, "max": 17.5, "male_min": 13.5, "female_min": 12.0},
    "wbc": {"unit": "10^3/uL", "min": 4.5, "max": 11.0},
    "platelets": {"unit": "10^3/uL", "min": 150, "max": 400},
    "glucose": {"unit": "mg/dL", "min": 70, "max": 100},
    "hba1c": {"unit": "%", "min": 4.0, "max": 5.6},
    "creatinine": {"unit": "mg/dL", "min": 0.7, "max": 1.3},
    "bun": {"unit": "mg/dL", "min": 7, "max": 20},
    "sodium": {"unit": "mEq/L", "min": 136, "max": 145},
    "potassium": {"unit": "mEq/L", "min": 3.5, "max": 5.0},
    "calcium": {"unit": "mg/dL", "min": 8.5, "max": 10.5},
    "total_cholesterol": {"unit": "mg/dL", "min": 0, "max": 200},
    "ldl": {"unit": "mg/dL", "min": 0, "max": 130},
    "hdl": {"unit": "mg/dL", "min": 40, "max": 100},
    "triglycerides": {"unit": "mg/dL", "min": 0, "max": 150},
    "tsh": {"unit": "mIU/L", "min": 0.4, "max": 4.0},
    "alt": {"unit": "U/L", "min": 7, "max": 56},
    "ast": {"unit": "U/L", "min": 10, "max": 40},
    "albumin": {"unit": "g/dL", "min": 3.5, "max": 5.5},
    "bilirubin": {"unit": "mg/dL", "min": 0.1, "max": 1.2},
    "iron": {"unit": "ug/dL", "min": 60, "max": 170},
    "ferritin": {"unit": "ng/mL", "min": 20, "max": 500},
    "vitamin_d": {"unit": "ng/mL", "min": 30, "max": 100},
    "vitamin_b12": {"unit": "pg/mL", "min": 200, "max": 900},
    "uric_acid": {"unit": "mg/dL", "min": 3.0, "max": 7.0},
    "esr": {"unit": "mm/hr", "min": 0, "max": 20},
    "crp": {"unit": "mg/L", "min": 0, "max": 3.0},
}


def classify_abnormality(value: float, ref_min: float, ref_max: float) -> dict:
    """Classify a lab value as normal, mildly/moderately/severely abnormal."""
    if ref_min <= value <= ref_max:
        return {"status": "normal", "severity": "none", "direction": "normal"}

    if value < ref_min:
        deficit_pct = ((ref_min - value) / ref_min) * 100
        direction = "low"
    else:
        deficit_pct = ((value - ref_max) / ref_max) * 100
        direction = "high"

    if deficit_pct <= 10:
        severity = "mild"
    elif deficit_pct <= 25:
        severity = "moderate"
    else:
        severity = "severe"

    return {"status": "abnormal", "severity": severity, "direction": direction, "deviation_pct": round(deficit_pct, 1)}


# OpenAI tool definitions

PARSE_LAB_VALUES_TOOL = {
    "type": "function",
    "function": {
        "name": "parse_lab_values",
        "description": "Parse and analyze lab values from a medical report. Returns structured data with reference ranges and abnormality flags.",
        "parameters": {
            "type": "object",
            "required": ["lab_values"],
            "properties": {
                "lab_values": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test_name": {"type": "string"},
                            "value": {"type": "number"},
                            "unit": {"type": "string"},
                        },
                        "required": ["test_name", "value"],
                    },
                    "description": "Array of lab values to analyze",
                },
            },
        },
    },
}

IDENTIFY_ABNORMALITIES_TOOL = {
    "type": "function",
    "function": {
        "name": "identify_abnormalities",
        "description": "Identify abnormal values from a set of lab results and classify severity.",
        "parameters": {
            "type": "object",
            "required": ["lab_values"],
            "properties": {
                "lab_values": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test_name": {"type": "string"},
                            "value": {"type": "number"},
                            "unit": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}


def parse_lab_values(lab_values: list[dict]) -> dict:
    """Parse lab values and add reference ranges + abnormality flags."""
    results = []
    for lv in lab_values:
        name = lv["test_name"].lower().replace(" ", "_").replace("-", "_")
        value = float(lv["value"])
        ref = REFERENCE_RANGES.get(name)

        if ref:
            classification = classify_abnormality(value, ref["min"], ref["max"])
            results.append({
                "test_name": lv["test_name"],
                "value": value,
                "unit": lv.get("unit", ref["unit"]),
                "reference_range": f"{ref['min']} - {ref['max']}",
                "reference_min": ref["min"],
                "reference_max": ref["max"],
                **classification,
            })
        else:
            results.append({
                "test_name": lv["test_name"],
                "value": value,
                "unit": lv.get("unit", ""),
                "reference_range": "Not available",
                "status": "unknown",
                "severity": "none",
            })

    return {
        "parsed_values": results,
        "total_tests": len(results),
        "abnormal_count": sum(1 for r in results if r.get("status") == "abnormal"),
    }


def identify_abnormalities(lab_values: list[dict]) -> dict:
    """Filter to only abnormal values with severity classification."""
    parsed = parse_lab_values(lab_values)
    abnormals = [v for v in parsed["parsed_values"] if v.get("status") == "abnormal"]

    return {
        "abnormal_values": abnormals,
        "total_abnormal": len(abnormals),
        "severe_count": sum(1 for v in abnormals if v.get("severity") == "severe"),
        "moderate_count": sum(1 for v in abnormals if v.get("severity") == "moderate"),
        "mild_count": sum(1 for v in abnormals if v.get("severity") == "mild"),
    }
