"""Few-shot examples and prompt templates for the Symptom Analyst Agent.

These examples demonstrate the expected input/output format and help the
model produce consistently structured responses. All patient data in
examples is fictional.
"""

SYMPTOM_ANALYSIS_FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "I've had a persistent headache for 3 days now. It's mostly on the "
            "right side and gets worse when I look at screens. I've also been "
            "feeling a bit nauseous."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "I'm sorry you're dealing with this headache. Let me ask a few "
            "follow-up questions to better understand your situation:\n\n"
            "1. How would you describe the pain — is it throbbing, pressing, "
            "or sharp?\n"
            "2. On a scale of 1-10, how severe is the pain?\n"
            "3. Have you noticed any sensitivity to light or sound?\n"
            "4. Have you had similar headaches before?\n"
            "5. Are you taking any medications currently?\n\n"
            "These details will help me provide a more accurate assessment."
        ),
    },
    {
        "role": "user",
        "content": (
            "It's a throbbing pain, about 7/10. Yes, I'm sensitive to light. "
            "I've had similar headaches a few times over the past year but "
            "never this long. I take lisinopril for blood pressure."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"differential_diagnoses": ['
            '{"condition": "Migraine without aura", "icd10_code": "G43.0", '
            '"likelihood": "high", "confidence": 0.78, '
            '"supporting_factors": ["unilateral throbbing pain", "photophobia", '
            '"nausea", "recurrent episodes", "worsened by screen use"], '
            '"ruling_out_factors": []}, '
            '{"condition": "Tension-type headache", "icd10_code": "G44.2", '
            '"likelihood": "medium", "confidence": 0.45, '
            '"supporting_factors": ["prolonged duration", "screen-related aggravation"], '
            '"ruling_out_factors": ["throbbing quality suggests migraine over tension"]}, '
            '{"condition": "Medication-related headache", "icd10_code": "G44.4", '
            '"likelihood": "low", "confidence": 0.2, '
            '"supporting_factors": ["on antihypertensive medication"], '
            '"ruling_out_factors": ["pattern predates medication changes"]}], '
            '"urgency_score": 4, '
            '"recommended_action": "Schedule an appointment with your doctor within '
            'the next few days. In the meantime, rest in a dark, quiet room and stay '
            'hydrated. Over-the-counter pain relief (acetaminophen or ibuprofen) may '
            'help. Seek immediate care if the headache suddenly becomes the worst '
            'you\'ve ever experienced, or if you develop vision changes, weakness, '
            'or difficulty speaking.", '
            '"recommended_specialist": "Neurology", '
            '"follow_up_questions": [], '
            '"sources": ["Clinical Guidelines — Headache Classification (IHS), p.12"]}'
        ),
    },
]


EMERGENCY_DETECTION_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "I'm having severe chest pain and my left arm feels numb. "
            "I'm sweating a lot and feel dizzy."
        ),
    },
    {
        "role": "assistant",
        "content": (
            '{"differential_diagnoses": ['
            '{"condition": "Acute myocardial infarction (heart attack)", '
            '"icd10_code": "I21.9", "likelihood": "high", "confidence": 0.85, '
            '"supporting_factors": ["severe chest pain", "left arm numbness", '
            '"diaphoresis", "dizziness"], "ruling_out_factors": []}], '
            '"urgency_score": 10, '
            '"recommended_action": "EMERGENCY: Call 911 immediately. These symptoms '
            'may indicate a heart attack. While waiting for emergency services: '
            'sit or lie down in a comfortable position, chew an aspirin (325mg) '
            'if you are not allergic, loosen tight clothing, and do not drive '
            'yourself to the hospital.", '
            '"recommended_specialist": null, '
            '"follow_up_questions": [], '
            '"sources": ["Emergency Medicine Guidelines — Chest Pain Evaluation, p.45"]}'
        ),
    },
]
