"""Specialty configuration — maps each AI doctor specialty to its domain.

Each specialty defines:
- display_name: Human-readable name
- description: What this specialist handles
- body_systems: Anatomical systems within scope
- common_conditions: Conditions this specialist treats
- common_tests: Tests this specialist typically orders
- red_flag_symptoms: Symptoms requiring immediate escalation
- out_of_scope_referrals: Map of out-of-scope keywords → correct specialty
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SpecialtyConfig:
    name: str
    display_name: str
    description: str
    body_systems: list[str] = field(default_factory=list)
    common_conditions: list[str] = field(default_factory=list)
    common_tests: list[str] = field(default_factory=list)
    red_flag_symptoms: list[str] = field(default_factory=list)
    out_of_scope_referrals: dict[str, str] = field(default_factory=dict)


SPECIALTIES: dict[str, SpecialtyConfig] = {
    "general_physician": SpecialtyConfig(
        name="general_physician",
        display_name="General Physician",
        description="Primary care doctor handling common illnesses, preventive care, and initial assessments.",
        body_systems=["general", "respiratory", "gastrointestinal", "musculoskeletal", "integumentary", "immune"],
        common_conditions=[
            "Common cold", "Flu", "Fever", "Allergies", "Minor infections",
            "Headache", "Fatigue", "Back pain", "UTI", "Gastroenteritis",
            "Hypertension", "Type 2 Diabetes", "Hyperlipidemia", "Anemia",
            "Vitamin deficiency", "Obesity", "Insomnia",
        ],
        common_tests=[
            "Complete Blood Count (CBC)", "Comprehensive Metabolic Panel (CMP)",
            "Lipid Panel", "Urinalysis", "Thyroid Function Test (TSH)",
            "HbA1c", "Chest X-Ray", "Basic Metabolic Panel (BMP)",
        ],
        red_flag_symptoms=[
            "Chest pain", "Difficulty breathing", "Loss of consciousness",
            "Sudden severe headache", "High fever >104F", "Uncontrolled bleeding",
        ],
        out_of_scope_referrals={
            "heart surgery": "cardiology",
            "brain tumor": "neurology",
            "fracture": "orthopedics",
            "pregnancy": "gynecology",
            "child illness": "pediatrics",
        },
    ),
    "cardiology": SpecialtyConfig(
        name="cardiology",
        display_name="Cardiologist",
        description="Heart and cardiovascular system specialist.",
        body_systems=["cardiovascular", "circulatory"],
        common_conditions=[
            "Hypertension", "Coronary Artery Disease", "Heart Failure",
            "Arrhythmia", "Atrial Fibrillation", "Valvular Heart Disease",
            "Angina", "Myocardial Infarction", "Peripheral Artery Disease",
            "Cardiomyopathy", "Deep Vein Thrombosis", "Pericarditis",
        ],
        common_tests=[
            "ECG/EKG", "Echocardiogram", "Stress Test", "Cardiac Catheterization",
            "Holter Monitor", "Lipid Panel", "Troponin", "BNP/NT-proBNP",
            "CT Angiography", "Coronary Calcium Score",
        ],
        red_flag_symptoms=[
            "Chest pain radiating to arm/jaw", "Sudden shortness of breath",
            "Irregular heartbeat with dizziness", "Fainting/syncope",
            "Severe swelling in legs", "Blue lips or fingers",
        ],
        out_of_scope_referrals={
            "headache": "neurology",
            "joint pain": "orthopedics",
            "skin rash": "dermatology",
            "stomach pain": "general_physician",
        },
    ),
    "orthopedics": SpecialtyConfig(
        name="orthopedics",
        display_name="Orthopedic Specialist",
        description="Bones, joints, muscles, ligaments, and musculoskeletal system specialist.",
        body_systems=["musculoskeletal", "skeletal", "articular"],
        common_conditions=[
            "Fractures", "Osteoarthritis", "Rheumatoid Arthritis",
            "Tendinitis", "Ligament tears (ACL, MCL)", "Carpal Tunnel",
            "Herniated Disc", "Scoliosis", "Rotator Cuff Injury",
            "Osteoporosis", "Bursitis", "Plantar Fasciitis", "Sciatica",
        ],
        common_tests=[
            "X-Ray", "MRI", "CT Scan", "Bone Density Scan (DEXA)",
            "Arthroscopy", "Electromyography (EMG)", "Nerve Conduction Study",
            "Rheumatoid Factor (RF)", "Anti-CCP Antibody", "Uric Acid Level",
        ],
        red_flag_symptoms=[
            "Open fracture with bone visible", "Loss of sensation in limbs",
            "Inability to move after injury", "Severe deformity after trauma",
            "Signs of compartment syndrome", "Spinal cord injury signs",
        ],
        out_of_scope_referrals={
            "chest pain": "cardiology",
            "headache": "neurology",
            "skin rash": "dermatology",
        },
    ),
    "gynecology": SpecialtyConfig(
        name="gynecology",
        display_name="Gynecologist",
        description="Female reproductive system, pregnancy, and women's health specialist.",
        body_systems=["reproductive", "endocrine", "urogenital"],
        common_conditions=[
            "PCOS", "Endometriosis", "Uterine Fibroids", "Menstrual Irregularities",
            "Pregnancy monitoring", "Preeclampsia", "Cervical dysplasia",
            "Ovarian cysts", "Pelvic inflammatory disease", "Menopause symptoms",
            "Infertility", "Gestational diabetes",
        ],
        common_tests=[
            "Pap Smear", "Pelvic Ultrasound", "Mammogram", "HPV Test",
            "Pregnancy Test (hCG)", "Hormonal Panel (FSH, LH, Estradiol)",
            "Glucose Tolerance Test", "STI Screening", "Colposcopy",
        ],
        red_flag_symptoms=[
            "Heavy vaginal bleeding", "Severe pelvic pain during pregnancy",
            "Signs of ectopic pregnancy", "Preeclampsia symptoms",
            "Sudden onset severe abdominal pain", "Decreased fetal movement",
        ],
        out_of_scope_referrals={
            "chest pain": "cardiology",
            "fracture": "orthopedics",
            "headache": "neurology",
        },
    ),
    "dermatology": SpecialtyConfig(
        name="dermatology",
        display_name="Dermatologist",
        description="Skin, hair, nails, and related conditions specialist.",
        body_systems=["integumentary", "immune"],
        common_conditions=[
            "Acne", "Eczema", "Psoriasis", "Dermatitis", "Skin Cancer",
            "Melanoma screening", "Rosacea", "Hives/Urticaria", "Fungal infections",
            "Vitiligo", "Alopecia", "Warts", "Shingles", "Cellulitis",
        ],
        common_tests=[
            "Skin Biopsy", "Patch Test (allergy)", "Dermatoscopy",
            "Wood's Lamp Examination", "KOH Preparation", "Skin Culture",
            "ANA Test (for lupus)", "IgE Level",
        ],
        red_flag_symptoms=[
            "Rapidly growing mole", "Non-healing wound", "Widespread rash with fever",
            "Signs of necrotizing fasciitis", "Severe allergic reaction with swelling",
            "Petechiae/purpura with systemic symptoms",
        ],
        out_of_scope_referrals={
            "chest pain": "cardiology",
            "joint pain": "orthopedics",
            "abdominal pain": "general_physician",
        },
    ),
    "pediatrics": SpecialtyConfig(
        name="pediatrics",
        display_name="Pediatrician",
        description="Children's health specialist for patients under 18.",
        body_systems=["general", "respiratory", "gastrointestinal", "neurological", "immune", "developmental"],
        common_conditions=[
            "Common cold in children", "Ear infections (Otitis Media)", "Croup",
            "Bronchiolitis", "Asthma in children", "ADHD", "Autism screening",
            "Growth delays", "Childhood obesity", "Vaccination schedule",
            "Hand foot mouth disease", "Chickenpox", "Measles",
        ],
        common_tests=[
            "Growth Chart Assessment", "Developmental Screening",
            "Hearing Test", "Vision Test", "CBC", "Lead Level",
            "Strep Test", "Urinalysis", "Stool Test",
        ],
        red_flag_symptoms=[
            "High fever in infant <3 months", "Difficulty breathing in child",
            "Severe dehydration signs", "Seizure in child", "Non-blanching rash",
            "Lethargy/unresponsiveness", "Bulging fontanelle in infant",
        ],
        out_of_scope_referrals={
            "adult symptoms": "general_physician",
            "pregnancy": "gynecology",
        },
    ),
    "neurology": SpecialtyConfig(
        name="neurology",
        display_name="Neurologist",
        description="Brain, spinal cord, and nervous system specialist.",
        body_systems=["neurological", "central nervous system", "peripheral nervous system"],
        common_conditions=[
            "Migraine", "Epilepsy", "Stroke", "Multiple Sclerosis",
            "Parkinson's Disease", "Alzheimer's Disease", "Neuropathy",
            "Vertigo", "Bell's Palsy", "Carpal Tunnel Syndrome",
            "Trigeminal Neuralgia", "Concussion", "Meningitis",
        ],
        common_tests=[
            "MRI Brain", "CT Head", "EEG", "Nerve Conduction Study",
            "Lumbar Puncture", "Carotid Ultrasound", "Neuropsychological Testing",
            "Evoked Potentials", "Electromyography (EMG)",
        ],
        red_flag_symptoms=[
            "Sudden severe headache (thunderclap)", "Facial drooping (stroke signs)",
            "Sudden vision loss", "Seizure (first-time)", "Loss of consciousness",
            "Sudden weakness on one side", "Slurred speech suddenly",
        ],
        out_of_scope_referrals={
            "chest pain": "cardiology",
            "skin rash": "dermatology",
            "joint pain": "orthopedics",
        },
    ),
    "psychiatry": SpecialtyConfig(
        name="psychiatry",
        display_name="Psychiatrist",
        description="Mental health, behavioral, and emotional disorders specialist.",
        body_systems=["neurological", "psychological", "behavioral"],
        common_conditions=[
            "Depression", "Anxiety Disorder", "Bipolar Disorder", "PTSD",
            "OCD", "Schizophrenia", "ADHD (adult)", "Panic Disorder",
            "Eating Disorders", "Insomnia", "Substance Use Disorder",
            "Social Anxiety", "Grief/Bereavement",
        ],
        common_tests=[
            "PHQ-9 (Depression Screening)", "GAD-7 (Anxiety Screening)",
            "AUDIT (Alcohol Screening)", "MMSE (Cognitive Screening)",
            "Thyroid Function (to rule out medical causes)", "Drug Screening",
            "Complete Blood Count", "Vitamin B12/Folate Levels",
        ],
        red_flag_symptoms=[
            "Suicidal ideation or plan", "Self-harm behavior",
            "Psychotic symptoms (hallucinations, delusions)",
            "Severe agitation or aggression", "Catatonia",
            "Acute intoxication or withdrawal",
        ],
        out_of_scope_referrals={
            "chest pain": "cardiology",
            "headache with neurological signs": "neurology",
            "skin rash": "dermatology",
        },
    ),
}


def get_specialty(name: str) -> SpecialtyConfig | None:
    """Look up a specialty by name."""
    return SPECIALTIES.get(name)


def get_all_specialties() -> list[dict[str, str]]:
    """Return a list of available specialties for frontend display."""
    return [
        {"name": s.name, "display_name": s.display_name, "description": s.description}
        for s in SPECIALTIES.values()
    ]


def match_specialty_from_symptoms(symptoms: list[str]) -> str:
    """Simple keyword matching to suggest a specialty from symptoms."""
    text = " ".join(symptoms).lower()
    keyword_map = {
        "cardiology": ["chest pain", "heart", "palpitation", "blood pressure", "cardiac"],
        "orthopedics": ["fracture", "bone", "joint", "knee", "back pain", "sprain", "shoulder"],
        "gynecology": ["pregnancy", "menstrual", "pcos", "vaginal", "breast", "period"],
        "dermatology": ["rash", "skin", "acne", "mole", "eczema", "psoriasis", "itching"],
        "pediatrics": ["child", "infant", "baby", "toddler", "pediatric"],
        "neurology": ["headache", "migraine", "seizure", "dizziness", "numbness", "tingling", "memory loss"],
        "psychiatry": ["anxiety", "depression", "panic", "suicidal", "insomnia", "mood", "stress", "hallucination"],
    }
    for specialty, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            return specialty
    return "general_physician"
