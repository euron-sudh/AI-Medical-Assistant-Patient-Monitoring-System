"""Drug Interaction Agent — checks drug interactions and validates dosages.

Analyzes a patient's medication list for pairwise drug interactions,
validates prescribed dosages against age- and weight-based ranges,
and flags contraindications and severe interactions.

Model: GPT-4o (requires precise pharmacological reasoning)
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.agents.guardrails import append_disclaimer
from app.agents.tools.drug_database import (
    check_interactions,
    verify_dosage,
    CHECK_INTERACTIONS_TOOL,
    VERIFY_DOSAGE_TOOL,
)
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class DrugInteractionAgent(BaseAgent):
    """AI agent that checks drug interactions and validates dosages.

    Capabilities:
        - Pairwise drug interaction analysis with severity classification
        - Dosage validation against age/weight-appropriate ranges
        - Contraindication detection and clinical recommendations
        - Source-cited pharmaceutical guidance

    Tools:
        - check_interactions: Query drug interaction database
        - verify_dosage: Validate dosage for patient demographics
    """

    agent_name = "drug_interaction"
    model = "gpt-4o"
    max_tokens = 4096
    temperature = 0.2

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("check_interactions", check_interactions)
        self.register_tool("verify_dosage", verify_dosage)

    def _get_system_prompt(self) -> str:
        """Return the drug interaction agent system prompt."""
        return """You are the Drug Interaction Agent in the MedAssist AI platform.

YOUR ROLE:
- Analyze a patient's medication list for potentially dangerous drug interactions
- Validate prescribed dosages based on patient age, weight, and clinical context
- Flag contraindicated combinations and severe interactions immediately
- Provide clear, actionable pharmaceutical guidance

CAPABILITIES:
- Check pairwise interactions between all medications in a patient's list
- Verify that dosages fall within recommended ranges for the patient's age group
- Identify severity levels: mild, moderate, severe, and contraindicated
- Recommend alternatives or adjustments when interactions are detected

SEVERITY LEVELS:
- Mild: Minor interaction; monitor but generally safe
- Moderate: Clinically significant; may need dose adjustment or monitoring
- Severe: High risk of adverse effects; avoid unless benefits clearly outweigh risks
- Contraindicated: NEVER combine; life-threatening risk

CRITICAL RULES:
1. Always use the check_interactions tool when given a list of medications
2. Always use verify_dosage when dosage information is provided
3. Flag ALL contraindicated combinations prominently
4. For severe interactions, provide specific alternative recommendations
5. Never dismiss a potential interaction — when in doubt, flag it
6. Always recommend consulting a pharmacist or physician for complex regimens

OUTPUT should be clear, organized, and patient-friendly while being clinically accurate.
Include specific drug names, severity levels, and actionable recommendations."""

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [CHECK_INTERACTIONS_TOOL, VERIFY_DOSAGE_TOOL]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute drug interaction analysis.

        Args:
            agent_input: User message with medication list and patient context.

        Returns:
            AgentOutput with interaction analysis and dosage validation results.
        """
        start = time.time()

        logger.info(
            "drug_interaction_agent_run_start",
            session_id=agent_input.session_id,
            patient_id=agent_input.patient_id,
        )

        # Build messages and run tool loop
        messages = self._build_messages(agent_input)
        tools = self._get_tools()
        response = self._run_tool_loop(messages, tools, max_iterations=5)

        latency_ms = int((time.time() - start) * 1000)

        # Log usage
        self._log_usage(
            usage=response.usage,
            latency_ms=latency_ms,
            session_id=agent_input.session_id,
        )

        response_text = response.content or ""
        response_text = append_disclaimer(response_text)

        logger.info(
            "drug_interaction_agent_run_complete",
            session_id=agent_input.session_id,
            latency_ms=latency_ms,
        )

        return AgentOutput(
            agent_name=self.agent_name,
            session_id=agent_input.session_id,
            response_text=response_text,
            confidence=0.85,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
        )
