"""Test Recommendation Tool — maps symptoms to appropriate medical tests.

Used by the SymptomAnalystAgent and SpecialtyAgent to recommend
relevant diagnostic tests based on reported symptoms.
"""

from __future__ import annotations

# Symptom-to-test mapping database
SYMPTOM_TEST_MAP: dict[str, list[dict[str, str]]] = {
    "chest pain": [
        {"test_name": "ECG/EKG", "test_code": "ECG", "reason": "Evaluate cardiac electrical activity", "urgency": "urgent"},
        {"test_name": "Troponin Level", "test_code": "TROP", "reason": "Check for heart muscle damage", "urgency": "urgent"},
        {"test_name": "Chest X-Ray", "test_code": "CXR", "reason": "Rule out pulmonary causes", "urgency": "urgent"},
        {"test_name": "D-Dimer", "test_code": "DDIM", "reason": "Screen for blood clots", "urgency": "urgent"},
    ],
    "headache": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for infection or anemia", "urgency": "routine"},
        {"test_name": "Blood Pressure Monitoring", "test_code": "BP", "reason": "Rule out hypertensive headache", "urgency": "routine"},
        {"test_name": "CT Head", "test_code": "CT-HEAD", "reason": "Rule out intracranial pathology if severe/sudden", "urgency": "urgent"},
        {"test_name": "ESR/CRP", "test_code": "ESR", "reason": "Check for inflammation markers", "urgency": "routine"},
    ],
    "fatigue": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for anemia or infection", "urgency": "routine"},
        {"test_name": "Thyroid Function Test (TSH)", "test_code": "TSH", "reason": "Rule out hypothyroidism", "urgency": "routine"},
        {"test_name": "Comprehensive Metabolic Panel", "test_code": "CMP", "reason": "Check organ function and electrolytes", "urgency": "routine"},
        {"test_name": "Iron Studies", "test_code": "IRON", "reason": "Check for iron deficiency", "urgency": "routine"},
        {"test_name": "Vitamin B12 and Folate", "test_code": "B12", "reason": "Check for vitamin deficiency", "urgency": "routine"},
    ],
    "fever": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check white blood cell count for infection", "urgency": "routine"},
        {"test_name": "Blood Culture", "test_code": "BCULT", "reason": "Identify bacterial infection in bloodstream", "urgency": "urgent"},
        {"test_name": "Urinalysis", "test_code": "UA", "reason": "Rule out urinary tract infection", "urgency": "routine"},
        {"test_name": "C-Reactive Protein", "test_code": "CRP", "reason": "Measure systemic inflammation", "urgency": "routine"},
    ],
    "shortness of breath": [
        {"test_name": "Chest X-Ray", "test_code": "CXR", "reason": "Evaluate lungs and heart", "urgency": "urgent"},
        {"test_name": "Pulse Oximetry", "test_code": "SPO2", "reason": "Measure blood oxygen levels", "urgency": "urgent"},
        {"test_name": "Pulmonary Function Test", "test_code": "PFT", "reason": "Assess lung capacity", "urgency": "routine"},
        {"test_name": "BNP/NT-proBNP", "test_code": "BNP", "reason": "Screen for heart failure", "urgency": "urgent"},
        {"test_name": "D-Dimer", "test_code": "DDIM", "reason": "Screen for pulmonary embolism", "urgency": "urgent"},
    ],
    "abdominal pain": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for infection or inflammation", "urgency": "routine"},
        {"test_name": "Comprehensive Metabolic Panel", "test_code": "CMP", "reason": "Check liver, kidney, and electrolytes", "urgency": "routine"},
        {"test_name": "Lipase", "test_code": "LIP", "reason": "Rule out pancreatitis", "urgency": "urgent"},
        {"test_name": "Abdominal Ultrasound", "test_code": "US-ABD", "reason": "Visualize abdominal organs", "urgency": "routine"},
        {"test_name": "Urinalysis", "test_code": "UA", "reason": "Rule out UTI or kidney stones", "urgency": "routine"},
    ],
    "joint pain": [
        {"test_name": "X-Ray of affected joint", "test_code": "XRAY", "reason": "Check for fracture or arthritis", "urgency": "routine"},
        {"test_name": "Rheumatoid Factor", "test_code": "RF", "reason": "Screen for rheumatoid arthritis", "urgency": "routine"},
        {"test_name": "Anti-CCP Antibody", "test_code": "CCP", "reason": "Confirm rheumatoid arthritis", "urgency": "routine"},
        {"test_name": "Uric Acid Level", "test_code": "UA-ACID", "reason": "Rule out gout", "urgency": "routine"},
        {"test_name": "ESR/CRP", "test_code": "ESR", "reason": "Measure inflammation", "urgency": "routine"},
    ],
    "dizziness": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for anemia", "urgency": "routine"},
        {"test_name": "Blood Glucose", "test_code": "GLU", "reason": "Rule out hypoglycemia", "urgency": "routine"},
        {"test_name": "Blood Pressure Monitoring", "test_code": "BP", "reason": "Check for orthostatic hypotension", "urgency": "routine"},
        {"test_name": "ECG", "test_code": "ECG", "reason": "Rule out cardiac arrhythmia", "urgency": "routine"},
    ],
    "cough": [
        {"test_name": "Chest X-Ray", "test_code": "CXR", "reason": "Rule out pneumonia or lung pathology", "urgency": "routine"},
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for infection", "urgency": "routine"},
        {"test_name": "Sputum Culture", "test_code": "SPCULT", "reason": "Identify respiratory infection", "urgency": "routine"},
        {"test_name": "Pulmonary Function Test", "test_code": "PFT", "reason": "Evaluate lung function if chronic", "urgency": "routine"},
    ],
    "skin rash": [
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Check for systemic infection", "urgency": "routine"},
        {"test_name": "Allergy Panel (IgE)", "test_code": "IGE", "reason": "Identify allergic triggers", "urgency": "routine"},
        {"test_name": "Skin Biopsy", "test_code": "BIOP", "reason": "Diagnose specific skin condition", "urgency": "routine"},
        {"test_name": "ANA Test", "test_code": "ANA", "reason": "Screen for autoimmune conditions", "urgency": "routine"},
    ],
    "weight gain": [
        {"test_name": "Thyroid Function Test", "test_code": "TSH", "reason": "Rule out hypothyroidism", "urgency": "routine"},
        {"test_name": "HbA1c", "test_code": "HBA1C", "reason": "Screen for diabetes", "urgency": "routine"},
        {"test_name": "Cortisol Level", "test_code": "CORT", "reason": "Rule out Cushing's syndrome", "urgency": "routine"},
        {"test_name": "Lipid Panel", "test_code": "LIPID", "reason": "Check cholesterol levels", "urgency": "routine"},
    ],
    "anxiety": [
        {"test_name": "Thyroid Function Test", "test_code": "TSH", "reason": "Rule out hyperthyroidism", "urgency": "routine"},
        {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Rule out medical causes", "urgency": "routine"},
        {"test_name": "Comprehensive Metabolic Panel", "test_code": "CMP", "reason": "Check electrolytes and glucose", "urgency": "routine"},
        {"test_name": "GAD-7 Screening", "test_code": "GAD7", "reason": "Standardized anxiety assessment", "urgency": "routine"},
    ],
    "depression": [
        {"test_name": "Thyroid Function Test", "test_code": "TSH", "reason": "Rule out hypothyroidism", "urgency": "routine"},
        {"test_name": "Vitamin D Level", "test_code": "VITD", "reason": "Low vitamin D linked to depression", "urgency": "routine"},
        {"test_name": "Vitamin B12", "test_code": "B12", "reason": "Deficiency can cause mood changes", "urgency": "routine"},
        {"test_name": "PHQ-9 Screening", "test_code": "PHQ9", "reason": "Standardized depression assessment", "urgency": "routine"},
    ],
}

# OpenAI function-calling tool definition
RECOMMEND_TESTS_TOOL = {
    "type": "function",
    "function": {
        "name": "recommend_tests",
        "description": "Recommend medical tests based on reported symptoms. Maps symptoms to appropriate diagnostic tests with urgency levels.",
        "parameters": {
            "type": "object",
            "required": ["symptoms"],
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of reported symptoms (e.g., ['chest pain', 'shortness of breath'])",
                },
                "patient_age": {
                    "type": "integer",
                    "description": "Patient age in years (affects test recommendations)",
                },
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe"],
                    "description": "Overall severity of the presentation",
                },
            },
        },
    },
}


def recommend_tests(
    symptoms: list[str],
    patient_age: int | None = None,
    severity: str = "moderate",
) -> dict:
    """Recommend medical tests based on symptoms.

    Returns a structured recommendation list with test names, codes,
    reasons, and urgency levels.
    """
    recommended: list[dict[str, str]] = []
    seen_codes: set[str] = set()

    for symptom in symptoms:
        symptom_lower = symptom.lower().strip()
        # Direct match
        if symptom_lower in SYMPTOM_TEST_MAP:
            for test in SYMPTOM_TEST_MAP[symptom_lower]:
                if test["test_code"] not in seen_codes:
                    # Upgrade urgency for severe presentations
                    t = dict(test)
                    if severity == "severe" and t["urgency"] == "routine":
                        t["urgency"] = "urgent"
                    recommended.append(t)
                    seen_codes.add(test["test_code"])
        else:
            # Partial match
            for key, tests in SYMPTOM_TEST_MAP.items():
                if key in symptom_lower or symptom_lower in key:
                    for test in tests:
                        if test["test_code"] not in seen_codes:
                            t = dict(test)
                            if severity == "severe" and t["urgency"] == "routine":
                                t["urgency"] = "urgent"
                            recommended.append(t)
                            seen_codes.add(test["test_code"])

    # Age-specific additions
    if patient_age and patient_age > 50 and not seen_codes.intersection({"LIPID", "HBA1C"}):
        recommended.append({"test_name": "Lipid Panel", "test_code": "LIPID", "reason": "Age-appropriate cardiovascular screening", "urgency": "routine"})
        recommended.append({"test_name": "HbA1c", "test_code": "HBA1C", "reason": "Age-appropriate diabetes screening", "urgency": "routine"})

    # Always include CBC if not already present (baseline)
    if "CBC" not in seen_codes and recommended:
        recommended.insert(0, {"test_name": "Complete Blood Count", "test_code": "CBC", "reason": "Baseline blood work", "urgency": "routine"})

    return {
        "recommended_tests": recommended[:10],  # Cap at 10 tests
        "total_tests": len(recommended),
        "symptoms_analyzed": symptoms,
        "severity": severity,
    }
