"""Symptom Analyst Agent — multi-turn symptom interview and differential diagnosis.

Conducts a structured symptom interview using the OLDCARTS framework, queries
the medical knowledge base for grounding, calculates urgency scores, and
produces a ranked differential diagnosis with source citations.

Model: GPT-4o (complex medical reasoning)
"""

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import (
    AgentInput,
    BaseAgent,
    SourceCitation,
    SymptomAnalysisResult,
)
from app.agents.prompts.system_prompts import SYMPTOM_ANALYST_SYSTEM_PROMPT
from app.agents.prompts.symptom_prompts import (
    EMERGENCY_DETECTION_EXAMPLES,
    SYMPTOM_ANALYSIS_FEW_SHOT_EXAMPLES,
)
from app.agents.tools.medical_kb import (
    QUERY_PATIENT_HISTORY_TOOL,
    SEARCH_MEDICAL_KB_TOOL,
    query_patient_history,
    search_medical_kb,
)
from app.agents.tools.urgency_scoring import (
    CALCULATE_URGENCY_SCORE_TOOL,
    RECOMMEND_SPECIALIST_TOOL,
    calculate_urgency_score,
    recommend_specialist,
)
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class SymptomAnalystAgent(BaseAgent):
    """Specialist agent for symptom analysis and differential diagnosis.

    Capabilities:
        - Multi-turn symptom interview with follow-up questions
        - Differential diagnosis ranked by likelihood and confidence
        - Urgency scoring with red-flag detection
        - Specialist referral recommendations
        - Source-cited responses grounded in medical knowledge base

    Tools:
        - search_medical_kb: Query RAG pipeline for medical knowledge
        - query_patient_history: Fetch patient medical history
        - calculate_urgency_score: Rule-based urgency scoring
        - recommend_specialist: Map symptoms to specialist type
    """

    agent_name = "symptom_analyst"
    model = "gpt-4o"
    max_tokens = 4096
    temperature = 0.3

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("search_medical_kb", search_medical_kb)
        self.register_tool("query_patient_history", query_patient_history)
        self.register_tool("calculate_urgency_score", calculate_urgency_score)
        self.register_tool("recommend_specialist", recommend_specialist)

    def _get_system_prompt(self) -> str:
        """Return the symptom analyst system prompt."""
        return SYMPTOM_ANALYST_SYSTEM_PROMPT

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [
            SEARCH_MEDICAL_KB_TOOL,
            QUERY_PATIENT_HISTORY_TOOL,
            CALCULATE_URGENCY_SCORE_TOOL,
            RECOMMEND_SPECIALIST_TOOL,
        ]

    def run(self, agent_input: AgentInput) -> SymptomAnalysisResult:
        """Execute symptom analysis.

        Builds a conversation with few-shot examples, runs the tool-calling
        loop, and parses the result into a structured SymptomAnalysisResult.

        Args:
            agent_input: User message with symptom description and patient context.

        Returns:
            SymptomAnalysisResult with differential diagnoses, urgency, and recommendations.
        """
        start_time = time.monotonic()

        logger.info(
            "symptom_analyst_run_start",
            session_id=agent_input.session_id,
            patient_id=agent_input.patient_id,
        )

        # Build messages with system prompt and few-shot examples
        messages = self._build_messages_with_examples(agent_input)

        # Run the tool-calling loop
        response = self._run_tool_loop(
            messages=messages,
            tools=self._get_tools(),
            max_iterations=5,
        )

        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Log usage
        self._log_usage(
            usage=response.usage,
            latency_ms=latency_ms,
            session_id=agent_input.session_id,
        )

        # Parse the response into structured output
        result = self._parse_result(
            response_content=response.content or "",
            session_id=agent_input.session_id,
            latency_ms=latency_ms,
            usage=response.usage,
        )

        logger.info(
            "symptom_analyst_run_complete",
            session_id=agent_input.session_id,
            urgency_score=result.urgency_score,
            diagnosis_count=len(result.differential_diagnoses),
            confidence=result.confidence,
            latency_ms=latency_ms,
        )

        return result

    def _build_messages_with_examples(
        self, agent_input: AgentInput
    ) -> list[dict[str, str]]:
        """Build message array with system prompt and few-shot examples.

        Includes the system prompt, few-shot examples for consistent output
        format, emergency detection examples, and the user's conversation.

        Args:
            agent_input: The agent input with user message and history.

        Returns:
            Messages array ready for the OpenAI API.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._get_system_prompt()},
        ]

        # Add few-shot examples
        messages.extend(SYMPTOM_ANALYSIS_FEW_SHOT_EXAMPLES)
        messages.extend(EMERGENCY_DETECTION_EXAMPLES)

        # Add conversation history
        for msg in agent_input.conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Add current user message
        messages.append({"role": "user", "content": agent_input.message})

        return messages

    def _parse_result(
        self,
        response_content: str,
        session_id: str,
        latency_ms: int,
        usage: Any,
    ) -> SymptomAnalysisResult:
        """Parse the LLM response into a structured SymptomAnalysisResult.

        Attempts to extract JSON from the response. Falls back to a
        conversational result if the response is not structured JSON
        (e.g., when the agent is asking follow-up questions).

        Args:
            response_content: Raw text content from the LLM response.
            session_id: Session identifier.
            latency_ms: Total run latency.
            usage: Token usage from the API call.

        Returns:
            Parsed SymptomAnalysisResult.
        """
        usage_dict = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }

        # Try to parse as structured JSON
        parsed = self._try_parse_json(response_content)

        if parsed and "differential_diagnoses" in parsed:
            return self._build_structured_result(
                parsed=parsed,
                session_id=session_id,
                latency_ms=latency_ms,
                usage_dict=usage_dict,
            )

        # Conversational response (follow-up questions, clarifications)
        return SymptomAnalysisResult(
            agent_name=self.agent_name,
            session_id=session_id,
            response_text=response_content,
            confidence=0.5,
            urgency_score=1,
            differential_diagnoses=[],
            recommended_action="Continue providing symptom details for analysis",
            follow_up_questions=[],
            usage=usage_dict,
            latency_ms=latency_ms,
        )

    def _build_structured_result(
        self,
        parsed: dict[str, Any],
        session_id: str,
        latency_ms: int,
        usage_dict: dict[str, int],
    ) -> SymptomAnalysisResult:
        """Build a SymptomAnalysisResult from parsed JSON.

        Args:
            parsed: Parsed JSON dict from the LLM response.
            session_id: Session identifier.
            latency_ms: Total run latency.
            usage_dict: Token usage dict.

        Returns:
            Fully populated SymptomAnalysisResult.
        """
        # Extract sources as SourceCitation objects
        sources = []
        for source_str in parsed.get("sources", []):
            sources.append(SourceCitation(
                source=source_str,
                document_type="clinical_guidelines",
            ))

        # Determine confidence from the top diagnosis
        diagnoses = parsed.get("differential_diagnoses", [])
        top_confidence = diagnoses[0].get("confidence", 0.5) if diagnoses else 0.5

        urgency_score = parsed.get("urgency_score", 5)
        escalation_required = urgency_score >= 8

        # Build human-readable response text
        response_text = self._format_patient_response(parsed)

        return SymptomAnalysisResult(
            agent_name=self.agent_name,
            session_id=session_id,
            response_text=response_text,
            confidence=top_confidence,
            sources=sources,
            escalation_required=escalation_required,
            differential_diagnoses=diagnoses,
            urgency_score=urgency_score,
            recommended_action=parsed.get("recommended_action", ""),
            recommended_specialist=parsed.get("recommended_specialist"),
            follow_up_questions=parsed.get("follow_up_questions", []),
            usage=usage_dict,
            latency_ms=latency_ms,
        )

    def _format_patient_response(self, parsed: dict[str, Any]) -> str:
        """Format the structured analysis into a patient-friendly response.

        Args:
            parsed: Parsed JSON analysis from the LLM.

        Returns:
            Plain-language summary suitable for patients.
        """
        parts = []

        diagnoses = parsed.get("differential_diagnoses", [])
        if diagnoses:
            parts.append("Based on your symptoms, here are the most likely possibilities:\n")
            for i, dx in enumerate(diagnoses[:3], 1):
                condition = dx.get("condition", "Unknown")
                likelihood = dx.get("likelihood", "unknown")
                parts.append(f"{i}. **{condition}** (likelihood: {likelihood})")

        action = parsed.get("recommended_action", "")
        if action:
            parts.append(f"\n**Recommended next step:** {action}")

        specialist = parsed.get("recommended_specialist")
        if specialist:
            parts.append(f"\n**Specialist referral:** {specialist}")

        sources = parsed.get("sources", [])
        if sources:
            parts.append(f"\n*Sources: {'; '.join(sources)}*")

        parts.append(
            "\n*This is an AI-assisted assessment, not a medical diagnosis. "
            "Please consult a healthcare provider for definitive evaluation.*"
        )

        return "\n".join(parts)

    @staticmethod
    def _try_parse_json(content: str) -> dict[str, Any] | None:
        """Attempt to parse JSON from the response content.

        Handles cases where the JSON is wrapped in markdown code blocks.

        Args:
            content: Raw response text that may contain JSON.

        Returns:
            Parsed dict if successful, None otherwise.
        """
        # Try direct parse
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting from markdown code block
        if "```json" in content:
            try:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

        if "```" in content:
            try:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except (json.JSONDecodeError, IndexError):
                pass

        return None
