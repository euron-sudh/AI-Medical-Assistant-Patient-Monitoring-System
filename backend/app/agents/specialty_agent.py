"""Specialty-based AI Agent — extends BaseAgent with medical domain boundaries.

Each SpecialtyAgent is constrained to its medical specialty and uses
domain-specific system prompts, tools, and guardrails.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.agents.base_agent import (
    AgentInput,
    AgentOutput,
    BaseAgent,
    SymptomAnalysisResult,
    ToolCall,
    ToolResult,
)
from app.agents.guardrails import run_all_guardrails, check_emergency
from app.agents.specialty_config import SpecialtyConfig, get_specialty, SPECIALTIES
from app.agents.tools.medical_kb import (
    search_medical_kb,
    SEARCH_MEDICAL_KB_TOOL,
    query_patient_history,
    QUERY_PATIENT_HISTORY_TOOL,
)
from app.agents.tools.urgency_scoring import (
    calculate_urgency_score,
    CALCULATE_URGENCY_SCORE_TOOL,
    recommend_specialist,
    RECOMMEND_SPECIALIST_TOOL,
)
from app.agents.tools.test_recommendation import (
    recommend_tests,
    RECOMMEND_TESTS_TOOL,
)


class SpecialtyAgent(BaseAgent):
    """An AI doctor agent constrained to a specific medical specialty."""

    agent_name = "specialty_agent"
    model = "gpt-4o-mini"
    temperature = 0.3
    max_tokens = 4096

    def __init__(self, specialty: str, openai_client=None):
        super().__init__(openai_client)
        self.specialty = specialty
        config = get_specialty(specialty)
        if not config:
            raise ValueError(f"Unknown specialty: {specialty}. Available: {list(SPECIALTIES.keys())}")
        self.config: SpecialtyConfig = config
        self.agent_name = f"specialty_{specialty}"

        # Register tools
        self.register_tool("search_medical_kb", search_medical_kb)
        self.register_tool("query_patient_history", query_patient_history)
        self.register_tool("calculate_urgency_score", calculate_urgency_score)
        self.register_tool("recommend_specialist", recommend_specialist)
        self.register_tool("recommend_tests", recommend_tests)

    def _get_system_prompt(self) -> str:
        conditions = ", ".join(self.config.common_conditions[:10])
        tests = ", ".join(self.config.common_tests[:8])
        red_flags = ", ".join(self.config.red_flag_symptoms[:6])
        body_systems = ", ".join(self.config.body_systems)

        return f"""You are an AI {self.config.display_name} specialist in the MedAssist AI platform.

SPECIALTY: {self.config.display_name}
DOMAIN: {self.config.description}
BODY SYSTEMS: {body_systems}

YOUR ROLE:
- Conduct thorough symptom interviews for conditions within your specialty
- Use the OLDCARTS framework: Onset, Location, Duration, Character, Alleviating/Aggravating, Radiation, Timing, Severity
- Ask 3-5 targeted follow-up questions before reaching conclusions
- Recommend appropriate medical tests based on symptoms
- Provide differential diagnoses with confidence levels
- Assess urgency and recommend appropriate actions

COMMON CONDITIONS YOU TREAT: {conditions}
TESTS YOU TYPICALLY ORDER: {tests}
RED-FLAG SYMPTOMS (escalate immediately): {red_flags}

DOMAIN BOUNDARIES:
- ONLY address conditions within your specialty scope
- If a patient asks about something outside your domain, clearly state it's outside your specialty
- Recommend the appropriate specialist for out-of-scope queries
- Never diagnose conditions outside {body_systems}

CRITICAL SAFETY RULES:
1. You are an AI assistant, NOT a real doctor
2. Never fabricate medical information
3. Never prescribe controlled substances
4. Always recommend professional consultation for serious conditions
5. For urgency scores 8-10: recommend emergency services immediately
6. Include disclaimer that this is AI-generated advice
7. If confidence is below 40%, clearly state uncertainty

WORKFLOW:
Phase 1 - SYMPTOM INTERVIEW: Ask targeted questions about the symptoms
Phase 2 - TEST RECOMMENDATION: Suggest relevant medical tests
Phase 3 - ASSESSMENT: Provide differential diagnoses with confidence scores

RESPONSE FORMAT (when providing assessment):
Return a JSON object:
{{
    "differential_diagnoses": [
        {{"condition": "Name", "confidence": 0.0-1.0, "reasoning": "Why"}}
    ],
    "urgency_score": 1-10,
    "recommended_action": "What the patient should do",
    "recommended_tests": [
        {{"test_name": "Name", "test_code": "CODE", "reason": "Why", "urgency": "routine|urgent"}}
    ],
    "recommended_specialist": "{self.config.display_name}",
    "follow_up_questions": ["question1", "question2"],
    "sources": [{{"source": "clinical guideline", "document_type": "guideline"}}]
}}

When asking follow-up questions (Phase 1), respond conversationally in plain language (6th-8th grade reading level).
Only return the JSON format when you have enough information for an assessment."""

    def _get_tools(self) -> list[dict[str, Any]]:
        return [
            SEARCH_MEDICAL_KB_TOOL,
            QUERY_PATIENT_HISTORY_TOOL,
            CALCULATE_URGENCY_SCORE_TOOL,
            RECOMMEND_SPECIALIST_TOOL,
            RECOMMEND_TESTS_TOOL,
        ]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()

        # Check for emergencies before anything
        emergency = check_emergency(agent_input.message)

        # Build messages and run tool loop
        messages = self._build_messages(agent_input)
        tools = self._get_tools()
        response = self._run_tool_loop(messages, tools, max_iterations=5)

        latency_ms = int((time.time() - start) * 1000)
        response_text = response.content or ""

        # Parse structured result if JSON
        result = self._parse_result(response_text, agent_input.session_id, latency_ms, response.usage)

        # Run guardrails on the response
        final_text, guardrail_result = run_all_guardrails(
            specialty_name=self.specialty,
            user_message=agent_input.message,
            response_text=result.response_text,
            confidence=result.confidence,
        )

        result.response_text = final_text
        result.escalation_required = guardrail_result.is_emergency or emergency.is_emergency

        if not guardrail_result.allowed and guardrail_result.refer_to:
            result.recommended_specialist = guardrail_result.refer_to

        return result

    def _parse_result(self, response_content: str, session_id: str, latency_ms: int, usage) -> SymptomAnalysisResult:
        """Parse LLM response into structured result."""
        parsed = self._try_parse_json(response_content)
        if parsed and "differential_diagnoses" in parsed:
            return SymptomAnalysisResult(
                agent_name=self.agent_name,
                session_id=session_id,
                response_text=self._format_patient_response(parsed),
                confidence=max((d.get("confidence", 0.5) for d in parsed["differential_diagnoses"]), default=0.5),
                differential_diagnoses=parsed.get("differential_diagnoses", []),
                urgency_score=parsed.get("urgency_score", 3),
                recommended_action=parsed.get("recommended_action", ""),
                recommended_specialist=parsed.get("recommended_specialist"),
                follow_up_questions=parsed.get("follow_up_questions", []),
                escalation_required=parsed.get("urgency_score", 0) >= 8,
                usage={"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens, "total_tokens": usage.total_tokens},
                latency_ms=latency_ms,
            )

        return SymptomAnalysisResult(
            agent_name=self.agent_name,
            session_id=session_id,
            response_text=response_content,
            confidence=0.7,
            urgency_score=3,
            usage={"prompt_tokens": usage.prompt_tokens, "completion_tokens": usage.completion_tokens, "total_tokens": usage.total_tokens},
            latency_ms=latency_ms,
        )

    def _format_patient_response(self, parsed: dict) -> str:
        """Format structured JSON into patient-friendly text."""
        parts = []

        if parsed.get("follow_up_questions"):
            parts.append("I'd like to understand your symptoms better. " + " ".join(parsed["follow_up_questions"][:3]))
            return "\n\n".join(parts)

        if parsed.get("differential_diagnoses"):
            parts.append("**Based on your symptoms, here's my assessment:**\n")
            for dx in parsed["differential_diagnoses"][:3]:
                conf = int(dx.get("confidence", 0) * 100)
                parts.append(f"- **{dx['condition']}** ({conf}% likelihood): {dx.get('reasoning', '')}")

        if parsed.get("recommended_tests"):
            parts.append("\n**Recommended Tests:**")
            for test in parsed["recommended_tests"]:
                urgency = f" ({test.get('urgency', 'routine')})" if test.get("urgency") else ""
                parts.append(f"- {test['test_name']}{urgency}: {test.get('reason', '')}")

        if parsed.get("recommended_action"):
            parts.append(f"\n**Recommended Action:** {parsed['recommended_action']}")

        urgency = parsed.get("urgency_score", 0)
        if urgency >= 8:
            parts.insert(0, "**URGENT:** Please seek immediate medical attention or call emergency services.\n")

        return "\n".join(parts)

    @staticmethod
    def _try_parse_json(text: str) -> dict | None:
        """Try to extract JSON from response text."""
        if not text:
            return None
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        # Try extracting from markdown code block
        if "```" in text:
            for block in text.split("```"):
                block = block.strip()
                if block.startswith("json"):
                    block = block[4:].strip()
                try:
                    return json.loads(block)
                except (json.JSONDecodeError, TypeError):
                    continue
        return None
