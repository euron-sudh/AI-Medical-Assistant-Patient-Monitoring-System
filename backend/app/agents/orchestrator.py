"""Agent Orchestrator — central router for dispatching requests to specialist agents.

Receives user requests, classifies intent using GPT-4o with function calling,
and routes to the appropriate specialist agent. Can invoke multiple agents
in parallel for complex queries.
"""

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import AgentInput, AgentOutput
from app.agents.prompts.system_prompts import ORCHESTRATOR_SYSTEM_PROMPT
from app.agents.symptom_analyst import SymptomAnalystAgent
from app.agents.report_reader import ReportReaderAgent
from app.agents.triage_agent import TriageAgent
from app.agents.specialty_agent import SpecialtyAgent
from app.agents.drug_interaction_agent import DrugInteractionAgent
from app.agents.voice_agent import VoiceAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.followup_agent import FollowUpAgent
from app.agents.specialty_config import match_specialty_from_symptoms, get_all_specialties
from app.integrations.openai_client import OpenAIClient, OpenAIClientError

logger = structlog.get_logger(__name__)


def _specialty_factory(specialty: str):
    """Create a factory class for a specialty agent."""
    class _Factory:
        model = "gpt-4o-mini"
        def __init__(self, openai_client=None):
            self._agent = SpecialtyAgent(specialty=specialty, openai_client=openai_client)
        def run(self, agent_input):
            return self._agent.run(agent_input)
    _Factory.__name__ = f"SpecialtyAgent_{specialty}"
    return _Factory


# Agent type to class mapping — all registered agents
AGENT_REGISTRY: dict[str, type] = {
    "symptom_analyst": SymptomAnalystAgent,
    "report_reader": ReportReaderAgent,
    "triage": TriageAgent,
    "drug_interaction": DrugInteractionAgent,
    "voice": VoiceAgent,
    "monitoring": MonitoringAgent,
    "follow_up": FollowUpAgent,
    # Specialty agents
    "general_physician": _specialty_factory("general_physician"),
    "cardiology": _specialty_factory("cardiology"),
    "orthopedics": _specialty_factory("orthopedics"),
    "gynecology": _specialty_factory("gynecology"),
    "dermatology": _specialty_factory("dermatology"),
    "pediatrics": _specialty_factory("pediatrics"),
    "neurology": _specialty_factory("neurology"),
    "psychiatry": _specialty_factory("psychiatry"),
}


class OrchestratorError(Exception):
    """Error during orchestration."""


class AgentOrchestrator:
    """Central router that classifies user intent and dispatches to specialist agents.

    The orchestrator:
    1. Receives the user's message and context
    2. Uses GPT-4o to classify the intent and select the target agent
    3. Instantiates and runs the selected specialist agent
    4. Returns the specialist agent's structured output

    For agent types not yet implemented, falls back to the SymptomAnalystAgent
    as the safest default for medical queries.
    """

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        """Initialize the orchestrator.

        Args:
            openai_client: OpenAI client for intent classification. Uses default if None.
        """
        if openai_client is None:
            from app.integrations.openai_client import openai_client as default_client
            self._client = default_client
        else:
            self._client = openai_client

    def route(self, agent_input: AgentInput) -> AgentOutput:
        """Classify the user's intent and route to the appropriate agent.

        Args:
            agent_input: User message with context and metadata.

        Returns:
            AgentOutput from the selected specialist agent.

        Raises:
            OrchestratorError: If routing fails and no fallback is available.
        """
        start_time = time.monotonic()

        logger.info(
            "orchestrator_route_start",
            session_id=agent_input.session_id,
            user_id=agent_input.user_id,
        )

        # Classify the intent
        classification = self._classify_intent(agent_input)
        agent_name = classification["agent"]
        routing_confidence = classification["confidence"]

        logger.info(
            "orchestrator_intent_classified",
            session_id=agent_input.session_id,
            target_agent=agent_name,
            confidence=routing_confidence,
            reasoning=classification.get("reasoning", ""),
        )

        # Get the agent class, fall back to symptom_analyst if not registered
        agent_class = AGENT_REGISTRY.get(agent_name)
        if agent_class is None:
            logger.warning(
                "orchestrator_agent_not_registered",
                requested_agent=agent_name,
                fallback_agent="symptom_analyst",
                session_id=agent_input.session_id,
            )
            agent_class = SymptomAnalystAgent

        # Instantiate and run the agent
        agent = agent_class(openai_client=self._client)
        result = agent.run(agent_input)

        latency_ms = int((time.monotonic() - start_time) * 1000)

        logger.info(
            "orchestrator_route_complete",
            session_id=agent_input.session_id,
            target_agent=agent_name,
            total_latency_ms=latency_ms,
        )

        return result

    def _classify_intent(self, agent_input: AgentInput) -> dict[str, Any]:
        """Classify the user's intent to determine the target agent.

        Uses GPT-4o-mini for fast classification. Falls back to
        symptom_analyst on any error.

        Args:
            agent_input: User input to classify.

        Returns:
            Dict with 'agent', 'confidence', and 'reasoning' keys.
        """
        messages = [
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": agent_input.message},
        ]

        try:
            response = self._client.chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=256,
                response_format={"type": "json_object"},
            )

            if response.content:
                parsed = json.loads(response.content)
                return {
                    "agent": parsed.get("agent", "symptom_analyst"),
                    "confidence": parsed.get("confidence", 0.5),
                    "reasoning": parsed.get("reasoning", ""),
                }

        except (OpenAIClientError, json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "orchestrator_classification_failed",
                error=str(exc),
                session_id=agent_input.session_id,
                fallback="symptom_analyst",
            )

        # Safe default: route to symptom analyst
        return {
            "agent": "symptom_analyst",
            "confidence": 0.5,
            "reasoning": "Fallback to symptom analyst due to classification error",
        }

    def get_available_agents(self) -> list[dict[str, str]]:
        """Return a list of currently registered agents.

        Returns:
            List of dicts with agent name and description.
        """
        return [
            {
                "name": name,
                "class": cls.__name__,
                "model": cls.model,
            }
            for name, cls in AGENT_REGISTRY.items()
        ]
