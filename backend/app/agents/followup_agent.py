"""Follow-Up Agent — care plan generation, adherence tracking, and scheduling.

Manages post-visit patient care by generating personalized care plans,
tracking medication and appointment adherence, and scheduling follow-up
appointments based on clinical guidelines.

Model: GPT-4o-mini (structured care plan generation)
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.agents.guardrails import append_disclaimer
from app.agents.tools.scheduling import (
    generate_care_plan,
    track_adherence,
    schedule_follow_up,
    GENERATE_CARE_PLAN_TOOL,
    TRACK_ADHERENCE_TOOL,
    SCHEDULE_FOLLOW_UP_TOOL,
)
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class FollowUpAgent(BaseAgent):
    """AI agent for post-visit care management and follow-up scheduling.

    Capabilities:
        - Personalized care plan generation based on diagnosis and patient profile
        - Medication and appointment adherence tracking
        - Automated follow-up appointment scheduling
        - Multi-morbidity care coordination guidance

    Tools:
        - generate_care_plan: Create personalized care plan from diagnosis
        - track_adherence: Check medication/appointment adherence
        - schedule_follow_up: Schedule follow-up appointment
    """

    agent_name = "follow_up"
    model = "gpt-4o-mini"
    max_tokens = 4096
    temperature = 0.3

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("generate_care_plan", generate_care_plan)
        self.register_tool("track_adherence", track_adherence)
        self.register_tool("schedule_follow_up", schedule_follow_up)

    def _get_system_prompt(self) -> str:
        """Return the follow-up agent system prompt."""
        return """You are the Follow-Up Agent in the MedAssist AI platform.

YOUR ROLE:
- Generate personalized care plans based on patient diagnosis and profile
- Track medication adherence and appointment compliance
- Schedule appropriate follow-up appointments
- Provide ongoing care management guidance

CAPABILITIES:
- generate_care_plan: Create a comprehensive care plan with lifestyle modifications,
  monitoring schedule, follow-up intervals, and red flags to watch for
- track_adherence: Check if a patient is following their medication and appointment schedule
- schedule_follow_up: Book follow-up appointments with specific timing and reason

CARE PLAN PRINCIPLES:
1. Personalize plans based on patient age, comorbidities, and medications
2. Include specific, measurable lifestyle modification goals
3. Define clear monitoring schedules with frequency
4. List red flags that warrant immediate medical attention
5. Account for polypharmacy in patients with multiple conditions

SCHEDULING GUIDELINES:
- Acute conditions: follow up in 3-7 days
- Chronic condition management: every 1-3 months
- Stable chronic conditions: every 3-6 months
- Post-procedure: within 1-2 weeks
- Medication changes: within 2-4 weeks

CRITICAL RULES:
1. Always use the appropriate tool for each task
2. Care plans must include red flags that require immediate attention
3. Consider the patient's full medical profile when creating plans
4. For patients on multiple medications, flag polypharmacy risks
5. Always recommend professional follow-up — never suggest AI-only management
6. Schedule follow-ups according to clinical guidelines, not patient preference alone

OUTPUT should be patient-friendly, actionable, and well-organized with clear next steps."""

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [GENERATE_CARE_PLAN_TOOL, TRACK_ADHERENCE_TOOL, SCHEDULE_FOLLOW_UP_TOOL]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute follow-up care management.

        Args:
            agent_input: User message with care plan request or follow-up query.

        Returns:
            AgentOutput with care plan, adherence report, or scheduling confirmation.
        """
        start = time.time()

        logger.info(
            "followup_agent_run_start",
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
            "followup_agent_run_complete",
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
