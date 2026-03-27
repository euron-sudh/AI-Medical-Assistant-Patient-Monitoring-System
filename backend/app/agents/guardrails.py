"""Agent Guardrails — safety enforcement across all AI agents.

Provides:
1. Domain boundary enforcement (specialty scope checking)
2. Controlled substance / high-risk medication blocking
3. Mandatory disclaimers
4. Confidence threshold enforcement
5. Emergency escalation detection
"""

from dataclasses import dataclass

from app.agents.specialty_config import get_specialty, match_specialty_from_symptoms

AI_DISCLAIMER = (
    "This is AI-generated advice and is not a substitute for professional medical diagnosis. "
    "Please consult a qualified healthcare provider for definitive diagnosis and treatment."
)

CONTROLLED_SUBSTANCES = {
    "oxycodone", "hydrocodone", "fentanyl", "morphine", "codeine",
    "methadone", "tramadol", "alprazolam", "diazepam", "lorazepam",
    "clonazepam", "amphetamine", "methylphenidate", "modafinil",
    "zolpidem", "suboxone", "buprenorphine", "ketamine",
}

EMERGENCY_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "want to die", "end my life",
    "chest pain", "can't breathe", "stroke", "heart attack",
    "severe bleeding", "unconscious", "overdose", "anaphylaxis",
    "seizure right now", "choking",
]

CONFIDENCE_THRESHOLD = 0.4  # Below this, agent must express uncertainty


@dataclass
class GuardrailResult:
    """Result of a guardrail check."""
    allowed: bool = True
    reason: str = ""
    refer_to: str | None = None
    is_emergency: bool = False
    modified_response: str | None = None


def check_domain_boundary(specialty_name: str, user_message: str) -> GuardrailResult:
    """Check if a query falls within a specialty's domain.

    Returns a GuardrailResult indicating if the agent should handle this
    or refer to a different specialty.
    """
    config = get_specialty(specialty_name)
    if not config:
        return GuardrailResult(allowed=True)

    message_lower = user_message.lower()
    for keyword, target_specialty in config.out_of_scope_referrals.items():
        if keyword.lower() in message_lower:
            return GuardrailResult(
                allowed=False,
                reason=f"This question is outside the scope of {config.display_name}.",
                refer_to=target_specialty,
            )
    return GuardrailResult(allowed=True)


def check_controlled_substance(response_text: str) -> GuardrailResult:
    """Check if the response attempts to prescribe controlled substances."""
    text_lower = response_text.lower()
    for substance in CONTROLLED_SUBSTANCES:
        if substance in text_lower and any(
            word in text_lower
            for word in ["prescribe", "recommend taking", "take", "dosage of"]
        ):
            return GuardrailResult(
                allowed=False,
                reason=(
                    f"AI cannot prescribe or recommend controlled substances like {substance}. "
                    "Please consult your doctor in person for this medication."
                ),
            )
    return GuardrailResult(allowed=True)


def check_emergency(user_message: str) -> GuardrailResult:
    """Detect emergency situations requiring immediate human intervention."""
    message_lower = user_message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in message_lower:
            return GuardrailResult(
                allowed=True,
                is_emergency=True,
                reason=f"Emergency keyword detected: '{keyword}'",
            )
    return GuardrailResult(allowed=True)


def enforce_confidence_threshold(confidence: float, response_text: str) -> str:
    """If confidence is below threshold, prepend uncertainty notice."""
    if confidence < CONFIDENCE_THRESHOLD:
        uncertainty = (
            "**Note:** I have low confidence in this assessment. "
            "The symptoms described are ambiguous and could indicate multiple conditions. "
            "I strongly recommend consulting a healthcare provider for proper evaluation.\n\n"
        )
        return uncertainty + response_text
    return response_text


def append_disclaimer(response_text: str) -> str:
    """Append the mandatory AI disclaimer to any agent response."""
    if AI_DISCLAIMER not in response_text:
        return response_text + f"\n\n---\n*{AI_DISCLAIMER}*"
    return response_text


def run_all_guardrails(
    specialty_name: str,
    user_message: str,
    response_text: str,
    confidence: float = 0.8,
) -> tuple[str, GuardrailResult]:
    """Run all guardrails on an agent response. Returns (final_response, result)."""

    # 1. Emergency check (always allow through but flag)
    emergency = check_emergency(user_message)

    # 2. Domain boundary check
    boundary = check_domain_boundary(specialty_name, user_message)
    if not boundary.allowed:
        referral_config = get_specialty(boundary.refer_to or "general_physician")
        referral_name = referral_config.display_name if referral_config else "General Physician"
        redirect_msg = (
            f"{boundary.reason} "
            f"I recommend consulting a **{referral_name}** for this concern.\n\n"
            f"Would you like me to connect you with our {referral_name} AI specialist?"
        )
        return append_disclaimer(redirect_msg), boundary

    # 3. Controlled substance check
    substance = check_controlled_substance(response_text)
    if not substance.allowed:
        return append_disclaimer(substance.reason), substance

    # 4. Confidence threshold
    response_text = enforce_confidence_threshold(confidence, response_text)

    # 5. Disclaimer
    response_text = append_disclaimer(response_text)

    return response_text, GuardrailResult(
        allowed=True,
        is_emergency=emergency.is_emergency,
    )
