"""Monitoring Agent — vitals anomaly detection and early warning scoring.

Analyzes patient vital signs in real-time, compares against normal/warning/critical
thresholds, computes NEWS2 (National Early Warning Score 2) for clinical risk
stratification, and detects worsening trends over time.

Model: GPT-4o-mini (fast response for real-time monitoring)
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.agents.guardrails import append_disclaimer
from app.agents.tools.vitals_analysis import (
    analyze_vitals,
    calculate_news2,
    detect_trend,
    ANALYZE_VITALS_TOOL,
    CALCULATE_NEWS2_TOOL,
    DETECT_TREND_TOOL,
)
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class MonitoringAgent(BaseAgent):
    """AI agent for patient vital sign monitoring and anomaly detection.

    Capabilities:
        - Real-time vital sign analysis against normal/warning/critical ranges
        - NEWS2 score calculation for clinical risk stratification
        - Trend detection to identify worsening patterns over time
        - Automated alerting for critical vital sign deviations

    Tools:
        - analyze_vitals: Compare vitals against thresholds
        - calculate_news2: Compute NEWS2 early warning score
        - detect_trend: Identify worsening vital sign trends
    """

    agent_name = "monitoring"
    model = "gpt-4o-mini"
    max_tokens = 3072
    temperature = 0.2

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("analyze_vitals", analyze_vitals)
        self.register_tool("calculate_news2", calculate_news2)
        self.register_tool("detect_trend", detect_trend)

    def _get_system_prompt(self) -> str:
        """Return the monitoring agent system prompt."""
        return """You are the Monitoring Agent in the MedAssist AI platform.

YOUR ROLE:
- Continuously analyze patient vital signs for anomalies
- Compute NEWS2 (National Early Warning Score 2) for clinical risk assessment
- Detect worsening trends that may indicate deterioration
- Alert clinical staff when vital signs breach critical thresholds

CAPABILITIES:
- analyze_vitals: Compare each vital sign against normal, warning, and critical ranges
- calculate_news2: Compute the standardized NEWS2 score from vital parameters
- detect_trend: Analyze historical vital data for worsening patterns

NEWS2 RISK LEVELS:
- Low (score 0): Routine monitoring every 12 hours
- Low-Medium (score 1-4): Increase monitoring to 4-hourly minimum
- Medium (score 5-6 or any single parameter = 3): Urgent review within 30 min
- High (score 7+): Emergency response, consider ICU transfer

CRITICAL RULES:
1. ALWAYS flag critical vital signs immediately — do not downplay
2. When multiple vitals are abnormal, compute NEWS2 to quantify risk
3. For NEWS2 >= 5, explicitly recommend urgent clinical review
4. For NEWS2 >= 7, recommend emergency response and ICU consideration
5. Always provide specific values and ranges in your analysis
6. Context matters: a heart rate of 55 may be normal for an athlete
7. When in doubt, escalate — patient safety is paramount

OUTPUT FORMAT:
- Clear summary of vital sign status
- Specific abnormalities with values and normal ranges
- NEWS2 score and risk level when applicable
- Recommended clinical response and monitoring frequency
- Any critical alerts prominently highlighted"""

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [ANALYZE_VITALS_TOOL, CALCULATE_NEWS2_TOOL, DETECT_TREND_TOOL]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute vital sign monitoring analysis.

        Args:
            agent_input: User message with vital sign data or monitoring request.

        Returns:
            AgentOutput with vitals analysis, NEWS2 score, and recommendations.
        """
        start = time.time()

        logger.info(
            "monitoring_agent_run_start",
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

        # Determine if escalation is needed based on metadata or response content
        escalation_required = agent_input.metadata.get("critical_vitals", False)

        logger.info(
            "monitoring_agent_run_complete",
            session_id=agent_input.session_id,
            latency_ms=latency_ms,
            escalation_required=escalation_required,
        )

        return AgentOutput(
            agent_name=self.agent_name,
            session_id=agent_input.session_id,
            response_text=response_text,
            confidence=0.9,
            escalation_required=escalation_required,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            latency_ms=latency_ms,
        )
