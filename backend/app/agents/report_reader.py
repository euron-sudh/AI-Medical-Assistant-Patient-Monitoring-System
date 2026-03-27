"""Report Reader Agent — analyzes medical reports and lab results.

Capabilities:
- Parse lab values from text reports
- Flag abnormalities with severity (mild/moderate/severe)
- Generate patient-friendly and clinical summaries
- Suggest follow-up tests based on findings
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.agents.base_agent import AgentInput, AgentOutput, BaseAgent
from app.agents.guardrails import append_disclaimer
from app.agents.tools.report_parsing import (
    parse_lab_values,
    identify_abnormalities,
    PARSE_LAB_VALUES_TOOL,
    IDENTIFY_ABNORMALITIES_TOOL,
)
from app.agents.tools.medical_kb import (
    search_medical_kb,
    SEARCH_MEDICAL_KB_TOOL,
    query_patient_history,
    QUERY_PATIENT_HISTORY_TOOL,
)
from app.agents.prompts.report_prompts import (
    REPORT_READER_SYSTEM_PROMPT,
    REPORT_READER_FEW_SHOT,
)


class ReportReaderAgent(BaseAgent):
    """AI agent that reads and analyzes medical reports."""

    agent_name = "report_reader"
    model = "gpt-4o-mini"
    temperature = 0.2
    max_tokens = 4096

    def __init__(self, openai_client=None):
        super().__init__(openai_client)
        self.register_tool("parse_lab_values", parse_lab_values)
        self.register_tool("identify_abnormalities", identify_abnormalities)
        self.register_tool("search_medical_kb", search_medical_kb)
        self.register_tool("query_patient_history", query_patient_history)

    def _get_system_prompt(self) -> str:
        return REPORT_READER_SYSTEM_PROMPT

    def _get_tools(self) -> list[dict[str, Any]]:
        return [
            PARSE_LAB_VALUES_TOOL,
            IDENTIFY_ABNORMALITIES_TOOL,
            SEARCH_MEDICAL_KB_TOOL,
            QUERY_PATIENT_HISTORY_TOOL,
        ]

    def run(self, agent_input: AgentInput) -> AgentOutput:
        start = time.time()

        # Build messages with few-shot examples
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        messages.extend(REPORT_READER_FEW_SHOT)
        for msg in agent_input.conversation_history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": agent_input.message})

        tools = self._get_tools()
        response = self._run_tool_loop(messages, tools, max_iterations=5)
        latency_ms = int((time.time() - start) * 1000)

        response_text = response.content or ""
        response_text = append_disclaimer(response_text)

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
