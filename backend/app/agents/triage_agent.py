"""Triage Agent — determines case severity and routes appropriately.

Decides: 'Can AI handle this case or does it need a human doctor?'

ESI (Emergency Severity Index) Levels:
- ESI 1: Immediate life-saving intervention needed
- ESI 2: High risk, confused/lethargic/disoriented, severe pain
- ESI 3: Multiple resources needed (labs, imaging, IV, etc.)
- ESI 4: One resource needed
- ESI 5: No resources needed (simple guidance)

Classification:
- EMERGENCY (ESI 1-2): Call 911 / Go to ER immediately
- SERIOUS (ESI 3): Needs human doctor within hours
- MODERATE (ESI 4): AI can help, schedule appointment
- ROUTINE (ESI 5): AI can handle fully
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.agents.guardrails import append_disclaimer, check_emergency, AI_DISCLAIMER
from app.agents.tools.urgency_scoring import (
    calculate_urgency_score,
    CALCULATE_URGENCY_TOOL,
    recommend_specialist,
    RECOMMEND_SPECIALIST_TOOL,
)


@dataclass
class TriageResult:
    esi_level: int  # 1-5
    classification: str  # EMERGENCY, SERIOUS, MODERATE, ROUTINE
    action: str
    needs_human_doctor: bool
    red_flags: list[str]
    reasoning: str


# Red-flag symptoms that require immediate human attention
RED_FLAG_DATABASE = {
    # Cardiac
    "chest pain": 2, "chest tightness": 2, "heart attack": 1,
    "palpitations with fainting": 1,
    # Respiratory
    "difficulty breathing": 2, "can't breathe": 1, "choking": 1,
    "severe shortness of breath": 1,
    # Neurological
    "stroke": 1, "facial drooping": 1, "sudden weakness one side": 1,
    "slurred speech": 2, "worst headache of life": 1, "seizure": 2,
    "loss of consciousness": 1, "sudden vision loss": 1,
    # Trauma
    "severe bleeding": 1, "open fracture": 1, "head injury": 2,
    "spinal injury": 1,
    # Psychiatric
    "suicidal": 1, "want to die": 1, "self harm": 2, "overdose": 1,
    # Other
    "anaphylaxis": 1, "severe allergic reaction": 1,
    "high fever infant": 1, "unresponsive": 1,
    "severe abdominal pain with fever": 2,
}


def calculate_esi(
    symptoms: list[str],
    severity: str = "moderate",
    vitals_abnormal: bool = False,
    patient_age: int | None = None,
) -> TriageResult:
    """Calculate ESI level and triage classification.

    Args:
        symptoms: List of reported symptoms
        severity: Patient-reported severity (mild/moderate/severe)
        vitals_abnormal: Whether vital signs are abnormal
        patient_age: Patient age for age-based adjustments

    Returns:
        TriageResult with ESI level, classification, and recommended action
    """
    text = " ".join(symptoms).lower()
    detected_red_flags = []
    min_esi = 5

    # Check against red-flag database
    for flag, esi in RED_FLAG_DATABASE.items():
        if flag in text:
            detected_red_flags.append(flag)
            min_esi = min(min_esi, esi)

    # Severity-based adjustment
    severity_map = {"mild": 5, "moderate": 4, "severe": 3}
    severity_esi = severity_map.get(severity, 4)
    min_esi = min(min_esi, severity_esi)

    # Abnormal vitals bump up urgency
    if vitals_abnormal and min_esi > 3:
        min_esi = 3

    # Age-based adjustment (very young or elderly)
    if patient_age is not None:
        if (patient_age < 3 or patient_age > 80) and min_esi > 3:
            min_esi -= 1

    # Clamp to valid range
    esi_level = max(1, min(5, min_esi))

    # Classify
    if esi_level <= 2:
        classification = "EMERGENCY"
        action = "Call 911 or go to the nearest emergency room IMMEDIATELY."
        needs_human = True
    elif esi_level == 3:
        classification = "SERIOUS"
        action = "Please see a doctor as soon as possible (within a few hours). Visit urgent care or your doctor today."
        needs_human = True
    elif esi_level == 4:
        classification = "MODERATE"
        action = "Schedule an appointment with your doctor within the next few days. AI can provide initial guidance."
        needs_human = False
    else:
        classification = "ROUTINE"
        action = "This can likely be managed with self-care and AI guidance. Schedule a routine visit if symptoms persist."
        needs_human = False

    reasoning = _build_reasoning(esi_level, detected_red_flags, severity, vitals_abnormal, patient_age)

    return TriageResult(
        esi_level=esi_level,
        classification=classification,
        action=action,
        needs_human_doctor=needs_human,
        red_flags=detected_red_flags,
        reasoning=reasoning,
    )


def _build_reasoning(esi: int, red_flags: list[str], severity: str, vitals_abnormal: bool, age: int | None) -> str:
    parts = [f"ESI Level {esi}/5 assessment:"]
    if red_flags:
        parts.append(f"Red flags detected: {', '.join(red_flags)}.")
    parts.append(f"Patient-reported severity: {severity}.")
    if vitals_abnormal:
        parts.append("Vital signs are abnormal.")
    if age is not None and (age < 3 or age > 80):
        parts.append(f"Age ({age}) is a risk factor.")
    return " ".join(parts)


class TriageAgent(BaseAgent):
    """AI agent that performs emergency triage and severity assessment."""

    agent_name = "triage"
    model = "gpt-4o-mini"
    temperature = 0.2
    max_tokens = 2048

    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.register_tool("calculate_urgency_score", calculate_urgency_score)
        self.register_tool("recommend_specialist", recommend_specialist)

    def _get_system_prompt(self) -> str:
        return """You are an AI Triage Agent in the MedAssist AI platform.

YOUR ROLE:
- Rapidly assess the severity of a patient's condition
- Determine if this case can be handled by AI or needs a human doctor
- Assign an ESI (Emergency Severity Index) level 1-5
- Route the patient appropriately

ESI LEVELS:
- ESI 1: Life-threatening, needs immediate intervention (cardiac arrest, respiratory failure)
- ESI 2: High-risk, altered mental status, severe pain/distress
- ESI 3: Needs multiple resources (labs + imaging + specialist)
- ESI 4: Needs one resource (single test or prescription)
- ESI 5: No resources needed (advice, education, OTC recommendation)

CLASSIFICATION:
- EMERGENCY (ESI 1-2): "Call 911 immediately" / "Go to ER now"
- SERIOUS (ESI 3): "See a doctor today" — transfer to human doctor
- MODERATE (ESI 4): "AI can help, but schedule appointment" — AI continues with caveat
- ROUTINE (ESI 5): "AI can handle this" — AI continues fully

CRITICAL RULES:
1. When in doubt, OVER-triage (assign higher severity)
2. Always check for red-flag symptoms
3. NEVER tell a potentially serious patient to "wait and see"
4. Chest pain, breathing difficulty, stroke signs, suicidal ideation → ALWAYS ESI 1-2
5. Include reasoning for your triage decision

OUTPUT FORMAT (JSON):
{
    "esi_level": 1-5,
    "classification": "EMERGENCY|SERIOUS|MODERATE|ROUTINE",
    "needs_human_doctor": true/false,
    "action": "What the patient should do right now",
    "red_flags_detected": ["list of red flags found"],
    "reasoning": "Why this triage level was assigned",
    "recommended_specialist": "specialist type if applicable"
}"""

    def _get_tools(self) -> list[dict[str, Any]]:
        return [CALCULATE_URGENCY_TOOL, RECOMMEND_SPECIALIST_TOOL]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()

        # Quick local triage first
        local_triage = calculate_esi(
            symptoms=[agent_input.message],
            severity=agent_input.metadata.get("severity", "moderate"),
            vitals_abnormal=agent_input.metadata.get("vitals_abnormal", False),
            patient_age=agent_input.metadata.get("patient_age"),
        )

        # For emergencies, respond immediately without LLM call
        if local_triage.esi_level <= 2:
            latency_ms = int((time.time() - start) * 1000)
            emergency_text = (
                f"**EMERGENCY — ESI Level {local_triage.esi_level}**\n\n"
                f"**{local_triage.action}**\n\n"
                f"Red flags detected: {', '.join(local_triage.red_flags) if local_triage.red_flags else 'Severe presentation'}\n\n"
                f"{local_triage.reasoning}\n\n"
                "If you are in immediate danger, please call **911** or your local emergency number right now."
            )
            return AgentOutput(
                agent_name=self.agent_name,
                session_id=agent_input.session_id,
                response_text=append_disclaimer(emergency_text),
                confidence=0.95,
                escalation_required=True,
                latency_ms=latency_ms,
            )

        # For non-emergencies, use LLM for more nuanced assessment
        messages = self._build_messages(agent_input)
        tools = self._get_tools()
        response = self._run_tool_loop(messages, tools, max_iterations=3)
        latency_ms = int((time.time() - start) * 1000)

        response_text = response.content or ""
        response_text = append_disclaimer(response_text)

        return AgentOutput(
            agent_name=self.agent_name,
            session_id=agent_input.session_id,
            response_text=response_text,
            confidence=0.8,
            escalation_required=local_triage.needs_human_doctor,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
        )
