"""Drug Interaction Database Tool — checks drug interactions and validates dosages.

Provides tools for the DrugInteractionAgent to check pairwise drug interactions,
validate dosages based on patient demographics, and query a built-in database
of common drug interaction pairs.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Drug Interaction Database — 20+ common interaction pairs
# Severity: mild | moderate | severe | contraindicated
# ---------------------------------------------------------------------------

DRUG_INTERACTIONS: dict[tuple[str, str], dict] = {
    # Anticoagulants
    ("warfarin", "aspirin"): {
        "severity": "severe",
        "effect": "Increased risk of bleeding due to additive anticoagulant effects",
        "recommendation": "Avoid combination unless specifically directed by physician; monitor INR closely",
    },
    ("warfarin", "ibuprofen"): {
        "severity": "severe",
        "effect": "NSAIDs increase anticoagulant effect and GI bleeding risk",
        "recommendation": "Avoid NSAIDs with warfarin; use acetaminophen for pain if needed",
    },
    ("warfarin", "amiodarone"): {
        "severity": "severe",
        "effect": "Amiodarone inhibits warfarin metabolism, significantly increasing INR",
        "recommendation": "Reduce warfarin dose by 30-50% when starting amiodarone; monitor INR frequently",
    },
    # Statins
    ("simvastatin", "amiodarone"): {
        "severity": "severe",
        "effect": "Increased risk of rhabdomyolysis due to elevated statin levels",
        "recommendation": "Limit simvastatin to 20mg/day with amiodarone; consider alternative statin",
    },
    ("simvastatin", "amlodipine"): {
        "severity": "moderate",
        "effect": "Amlodipine increases simvastatin exposure, raising myopathy risk",
        "recommendation": "Limit simvastatin to 20mg/day with amlodipine",
    },
    ("atorvastatin", "clarithromycin"): {
        "severity": "severe",
        "effect": "CYP3A4 inhibition increases statin levels and rhabdomyolysis risk",
        "recommendation": "Suspend statin during clarithromycin course or use azithromycin instead",
    },
    # ACE Inhibitors / ARBs
    ("lisinopril", "spironolactone"): {
        "severity": "moderate",
        "effect": "Hyperkalemia risk due to potassium-sparing effects of both drugs",
        "recommendation": "Monitor serum potassium closely; avoid potassium supplements",
    },
    ("lisinopril", "potassium"): {
        "severity": "moderate",
        "effect": "ACE inhibitors reduce potassium excretion; supplements may cause hyperkalemia",
        "recommendation": "Monitor potassium levels; avoid supplements unless directed",
    },
    # SSRIs / MAOIs
    ("fluoxetine", "phenelzine"): {
        "severity": "contraindicated",
        "effect": "Serotonin syndrome risk — potentially fatal hyperthermia, rigidity, myoclonus",
        "recommendation": "NEVER combine SSRIs with MAOIs; 5-week washout required for fluoxetine",
    },
    ("sertraline", "tramadol"): {
        "severity": "severe",
        "effect": "Increased risk of serotonin syndrome and seizures",
        "recommendation": "Avoid combination; use alternative analgesic without serotonergic activity",
    },
    ("fluoxetine", "tramadol"): {
        "severity": "severe",
        "effect": "Risk of serotonin syndrome due to additive serotonergic effects",
        "recommendation": "Avoid combination; consider non-serotonergic analgesics",
    },
    # Metformin
    ("metformin", "contrast_dye"): {
        "severity": "severe",
        "effect": "Risk of lactic acidosis when metformin is used with iodinated contrast",
        "recommendation": "Hold metformin 48h before and after contrast administration; check renal function",
    },
    ("metformin", "alcohol"): {
        "severity": "moderate",
        "effect": "Increased risk of lactic acidosis and hypoglycemia",
        "recommendation": "Limit alcohol intake; avoid binge drinking",
    },
    # Blood pressure
    ("amlodipine", "grapefruit"): {
        "severity": "moderate",
        "effect": "Grapefruit inhibits CYP3A4, increasing amlodipine levels and hypotension risk",
        "recommendation": "Avoid grapefruit juice; monitor blood pressure",
    },
    # Antibiotics
    ("metronidazole", "alcohol"): {
        "severity": "severe",
        "effect": "Disulfiram-like reaction: severe nausea, vomiting, flushing, tachycardia",
        "recommendation": "Absolutely avoid alcohol during and 48h after metronidazole treatment",
    },
    ("ciprofloxacin", "antacids"): {
        "severity": "moderate",
        "effect": "Antacids reduce ciprofloxacin absorption by up to 90%",
        "recommendation": "Take ciprofloxacin 2h before or 6h after antacids",
    },
    ("ciprofloxacin", "theophylline"): {
        "severity": "severe",
        "effect": "Ciprofloxacin inhibits theophylline metabolism, risking toxicity",
        "recommendation": "Monitor theophylline levels; reduce dose or use alternative antibiotic",
    },
    # Cardiac
    ("digoxin", "amiodarone"): {
        "severity": "severe",
        "effect": "Amiodarone increases digoxin levels by 70-100%, risking toxicity",
        "recommendation": "Reduce digoxin dose by 50% when starting amiodarone; monitor levels",
    },
    ("digoxin", "verapamil"): {
        "severity": "severe",
        "effect": "Verapamil increases digoxin levels and additive AV node depression",
        "recommendation": "Reduce digoxin dose; monitor levels and heart rate",
    },
    # Diabetes
    ("glipizide", "fluconazole"): {
        "severity": "moderate",
        "effect": "Fluconazole inhibits glipizide metabolism, increasing hypoglycemia risk",
        "recommendation": "Monitor blood glucose closely; may need to reduce glipizide dose",
    },
    # Thyroid
    ("levothyroxine", "calcium"): {
        "severity": "moderate",
        "effect": "Calcium reduces levothyroxine absorption",
        "recommendation": "Separate administration by at least 4 hours",
    },
    ("levothyroxine", "iron"): {
        "severity": "moderate",
        "effect": "Iron reduces levothyroxine absorption",
        "recommendation": "Separate administration by at least 4 hours",
    },
    # Respiratory
    ("theophylline", "erythromycin"): {
        "severity": "severe",
        "effect": "Erythromycin inhibits theophylline metabolism, risking seizures and arrhythmias",
        "recommendation": "Monitor theophylline levels; consider alternative antibiotic",
    },
}


# ---------------------------------------------------------------------------
# Dosage reference database
# ---------------------------------------------------------------------------

DOSAGE_RANGES: dict[str, dict] = {
    "metformin": {
        "unit": "mg",
        "adult_min": 500,
        "adult_max": 2550,
        "pediatric_min": 500,
        "pediatric_max": 2000,
        "elderly_max": 2000,
        "renal_adjustment": True,
        "notes": "Start low, titrate gradually; take with meals",
    },
    "lisinopril": {
        "unit": "mg",
        "adult_min": 2.5,
        "adult_max": 40,
        "pediatric_min": 0.07,
        "pediatric_max": 0.6,
        "elderly_max": 40,
        "renal_adjustment": True,
        "notes": "Monitor potassium and renal function",
    },
    "amlodipine": {
        "unit": "mg",
        "adult_min": 2.5,
        "adult_max": 10,
        "pediatric_min": 2.5,
        "pediatric_max": 5,
        "elderly_max": 10,
        "renal_adjustment": False,
        "notes": "Start at 5mg for most adults",
    },
    "atorvastatin": {
        "unit": "mg",
        "adult_min": 10,
        "adult_max": 80,
        "pediatric_min": 10,
        "pediatric_max": 20,
        "elderly_max": 80,
        "renal_adjustment": False,
        "notes": "Monitor LFTs; can be taken any time of day",
    },
    "omeprazole": {
        "unit": "mg",
        "adult_min": 10,
        "adult_max": 40,
        "pediatric_min": 5,
        "pediatric_max": 20,
        "elderly_max": 40,
        "renal_adjustment": False,
        "notes": "Take 30-60 min before meals; limit long-term use",
    },
    "amoxicillin": {
        "unit": "mg",
        "adult_min": 250,
        "adult_max": 1500,
        "pediatric_min": 25,
        "pediatric_max": 90,
        "elderly_max": 1500,
        "renal_adjustment": True,
        "notes": "Pediatric doses are mg/kg/day; check for penicillin allergy",
    },
    "ibuprofen": {
        "unit": "mg",
        "adult_min": 200,
        "adult_max": 3200,
        "pediatric_min": 5,
        "pediatric_max": 40,
        "elderly_max": 2400,
        "renal_adjustment": True,
        "notes": "Take with food; avoid in renal impairment; pediatric dose is mg/kg/day",
    },
    "acetaminophen": {
        "unit": "mg",
        "adult_min": 325,
        "adult_max": 4000,
        "pediatric_min": 10,
        "pediatric_max": 75,
        "elderly_max": 3000,
        "renal_adjustment": False,
        "notes": "Max 4g/day adults; reduce with liver disease; pediatric dose is mg/kg/day",
    },
}


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions
# ---------------------------------------------------------------------------

CHECK_INTERACTIONS_TOOL = {
    "type": "function",
    "function": {
        "name": "check_interactions",
        "description": (
            "Check for pairwise drug interactions among a list of medications. "
            "Returns interaction details including severity (mild/moderate/severe/contraindicated), "
            "clinical effect, and recommendations for each interacting pair."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "drugs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of drug names to check for interactions",
                },
            },
            "required": ["drugs"],
        },
    },
}

VERIFY_DOSAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "verify_dosage",
        "description": (
            "Validate whether a prescribed dosage is within the recommended range "
            "for a given drug, considering the patient's age and weight. Returns "
            "whether the dosage is within range, below, or above recommended limits."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "Name of the medication",
                },
                "dosage": {
                    "type": "number",
                    "description": "Prescribed dosage amount in the drug's standard unit",
                },
                "patient_age": {
                    "type": "integer",
                    "description": "Patient age in years",
                },
                "patient_weight": {
                    "type": "number",
                    "description": "Patient weight in kilograms",
                },
            },
            "required": ["drug_name", "dosage", "patient_age", "patient_weight"],
        },
    },
}


# ---------------------------------------------------------------------------
# Tool handler functions
# ---------------------------------------------------------------------------


def check_interactions(drugs: list[str]) -> dict:
    """Check for pairwise drug interactions among the provided medications.

    Args:
        drugs: List of drug names to check.

    Returns:
        Dict with interaction results for each pair.
    """
    normalized = [d.strip().lower() for d in drugs]
    interactions_found = []
    checked_pairs = []

    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            drug_a, drug_b = normalized[i], normalized[j]
            pair_key = (drug_a, drug_b)
            reverse_key = (drug_b, drug_a)
            checked_pairs.append(f"{drug_a} + {drug_b}")

            interaction = DRUG_INTERACTIONS.get(pair_key) or DRUG_INTERACTIONS.get(reverse_key)

            if interaction:
                interactions_found.append({
                    "drug_a": drug_a,
                    "drug_b": drug_b,
                    "severity": interaction["severity"],
                    "effect": interaction["effect"],
                    "recommendation": interaction["recommendation"],
                })

    logger.info(
        "drug_interactions_checked",
        drug_count=len(drugs),
        pairs_checked=len(checked_pairs),
        interactions_found=len(interactions_found),
    )

    return {
        "drugs_checked": normalized,
        "pairs_checked": checked_pairs,
        "interactions_found": interactions_found,
        "total_interactions": len(interactions_found),
        "has_contraindications": any(
            i["severity"] == "contraindicated" for i in interactions_found
        ),
        "has_severe": any(
            i["severity"] == "severe" for i in interactions_found
        ),
    }


def verify_dosage(
    drug_name: str,
    dosage: float,
    patient_age: int,
    patient_weight: float,
) -> dict:
    """Validate a prescribed dosage against recommended ranges.

    Args:
        drug_name: Name of the medication.
        dosage: Prescribed dosage amount.
        patient_age: Patient age in years.
        patient_weight: Patient weight in kilograms.

    Returns:
        Dict with validation result, status, and recommendations.
    """
    name = drug_name.strip().lower()
    drug_info = DOSAGE_RANGES.get(name)

    if not drug_info:
        logger.warning("drug_not_in_database", drug_name=name)
        return {
            "drug_name": name,
            "dosage": dosage,
            "unit": "unknown",
            "status": "unknown",
            "message": f"Drug '{name}' not found in dosage database. Please verify with a pharmacist.",
            "in_range": None,
        }

    # Determine age group and appropriate range
    is_pediatric = patient_age < 18
    is_elderly = patient_age >= 65

    if is_pediatric:
        dose_min = drug_info["pediatric_min"]
        dose_max = drug_info["pediatric_max"]
        age_group = "pediatric"
    elif is_elderly:
        dose_min = drug_info["adult_min"]
        dose_max = drug_info.get("elderly_max", drug_info["adult_max"])
        age_group = "elderly"
    else:
        dose_min = drug_info["adult_min"]
        dose_max = drug_info["adult_max"]
        age_group = "adult"

    # Evaluate dosage
    if dosage < dose_min:
        status = "below_range"
        message = f"Dosage {dosage}{drug_info['unit']} is below the recommended minimum of {dose_min}{drug_info['unit']} for {age_group} patients."
        in_range = False
    elif dosage > dose_max:
        status = "above_range"
        message = f"Dosage {dosage}{drug_info['unit']} exceeds the recommended maximum of {dose_max}{drug_info['unit']} for {age_group} patients."
        in_range = False
    else:
        status = "within_range"
        message = f"Dosage {dosage}{drug_info['unit']} is within the recommended range ({dose_min}-{dose_max}{drug_info['unit']}) for {age_group} patients."
        in_range = True

    logger.info(
        "dosage_verified",
        drug_name=name,
        dosage=dosage,
        status=status,
        age_group=age_group,
    )

    return {
        "drug_name": name,
        "dosage": dosage,
        "unit": drug_info["unit"],
        "age_group": age_group,
        "recommended_min": dose_min,
        "recommended_max": dose_max,
        "status": status,
        "in_range": in_range,
        "message": message,
        "notes": drug_info.get("notes", ""),
        "renal_adjustment_needed": drug_info.get("renal_adjustment", False),
    }
