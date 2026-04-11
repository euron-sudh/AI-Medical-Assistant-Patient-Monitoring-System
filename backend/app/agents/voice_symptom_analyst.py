"""Voice Symptom Analyst Agent — conversational voice-based symptom assessment.

Combines voice interaction (Whisper STT + OpenAI TTS) with symptom analysis
to create an interactive, conversational medical interview experience.

Model: GPT-4o (complex medical reasoning + voice conversation)
"""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from app.agents.base_agent import (
    AgentInput,
    BaseAgent,
    SymptomAnalysisResult,
    SourceCitation,
)
from app.agents.prompts.symptom_prompts import (
    EMERGENCY_DETECTION_EXAMPLES,
    SYMPTOM_ANALYSIS_FEW_SHOT_EXAMPLES,
)
from app.agents.tools.medical_kb import (
    SEARCH_MEDICAL_KB_TOOL,
    QUERY_PATIENT_HISTORY_TOOL,
    search_medical_kb,
    query_patient_history,
)
from app.agents.tools.urgency_scoring import (
    CALCULATE_URGENCY_SCORE_TOOL,
    RECOMMEND_SPECIALIST_TOOL,
    calculate_urgency_score,
    recommend_specialist,
)
from app.agents.tools.test_recommendation import (
    recommend_tests,
    RECOMMEND_TESTS_TOOL,
)
from app.integrations.openai_client import OpenAIClient

logger = structlog.get_logger(__name__)


class VoiceSymptomAnalystAgent(BaseAgent):
    """Voice-based symptom analysis agent with conversational interview.

    Capabilities:
        - Multi-turn voice conversation for symptom assessment
        - Real-time transcription via Whisper
        - Natural voice responses via OpenAI TTS
        - Differential diagnosis with source citations
        - Medical test recommendations
        - Urgency scoring and specialist referrals

    Tools:
        - search_medical_kb: Query RAG for medical knowledge
        - query_patient_history: Fetch patient medical history
        - calculate_urgency_score: Rule-based urgency scoring
        - recommend_specialist: Map symptoms to specialist type
        - recommend_tests: Suggest diagnostic tests based on symptoms
    """

    agent_name = "voice_symptom_analyst"
    model = "gpt-4o"
    max_tokens = 4096
    temperature = 0.3
    voice_preset = "nova"  # Warm, conversational voice

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        super().__init__(openai_client=openai_client)

        # Register tool handlers
        self.register_tool("search_medical_kb", search_medical_kb)
        self.register_tool("query_patient_history", query_patient_history)
        self.register_tool("calculate_urgency_score", calculate_urgency_score)
        self.register_tool("recommend_specialist", recommend_specialist)
        self.register_tool("recommend_tests", recommend_tests)

    def _get_system_prompt(self) -> str:
        """Return the voice symptom analyst system prompt."""
        return """You are a compassionate AI doctor conducting a voice-based symptom assessment.

YOUR ROLE:
- Conduct a natural, conversational symptom interview via voice
- Ask follow-up questions one at a time (not in lists)
- Use the OLDCARTS framework naturally in conversation
- Build a differential diagnosis based on patient responses
- Recommend appropriate medical tests
- Assess urgency and provide clear next steps

CONVERSATION STYLE:
- Speak naturally, as a real doctor would
- Use warm, empathetic language
- Ask one follow-up question at a time (not multiple)
- Use plain language at a 6th-8th grade reading level
- Explain medical terms when necessary
- Keep responses concise (2-4 sentences for follow-ups)

CRITICAL SAFETY RULES:
- You are an AI assistant, NOT a real doctor
- Never fabricate medical information
- Always cite sources when providing medical information
- For emergency symptoms: immediately recommend calling 911
- Express uncertainty when confidence is low

INTERVIEW FLOW:
1. Start by asking what symptoms the patient is experiencing
2. Ask targeted follow-up questions based on their response
3. Consider: onset, location, duration, character, severity, aggravating/alleviating factors
4. Factor in patient's medical history and current medications
5. When you have sufficient information, provide assessment and recommendations

OUTPUT FORMAT:
When concluding the assessment, provide structured JSON:
{
  "differential_diagnoses": [...],
  "urgency_score": 1-10,
  "recommended_action": "...",
  "recommended_specialist": "...",
  "recommended_tests": ["test1", "test2"],
  "sources": ["citation1", "citation2"]
}

VOICE-SPECIFIC GUIDELINES:
- Use conversational language (e.g., "I see" instead of "Understood")
- Pause naturally between questions
- Acknowledge patient responses before asking follow-ups
- Use verbal cues like "Let me think about that for a moment" when processing"""

    def _get_tools(self) -> list[dict[str, Any]]:
        """Return tool definitions for OpenAI function calling."""
        return [
            SEARCH_MEDICAL_KB_TOOL,
            QUERY_PATIENT_HISTORY_TOOL,
            CALCULATE_URGENCY_SCORE_TOOL,
            RECOMMEND_SPECIALIST_TOOL,
            RECOMMEND_TESTS_TOOL,
        ]

    def run(self, agent_input: AgentInput) -> SymptomAnalysisResult:
        """Execute voice-based symptom analysis.

        Args:
            agent_input: User message with symptom description and context.

        Returns:
            SymptomAnalysisResult with diagnoses, urgency, and recommendations.
        """
        start_time = time.monotonic()

        logger.info(
            "voice_symptom_analyst_run_start",
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

        # Parse the response
        result = self._parse_result(
            response_content=response.content or "",
            session_id=agent_input.session_id,
            latency_ms=latency_ms,
            usage=response.usage,
        )

        logger.info(
            "voice_symptom_analyst_run_complete",
            session_id=agent_input.session_id,
            urgency_score=result.urgency_score,
            diagnosis_count=len(result.differential_diagnoses),
            latency_ms=latency_ms,
        )

        return result

    def _build_messages_with_examples(
        self, agent_input: AgentInput
    ) -> list[dict[str, str]]:
        """Build message array with system prompt and few-shot examples."""
        messages = [{"role": "system", "content": self._get_system_prompt()}]
        
        # Add few-shot examples
        messages.extend(SYMPTOM_ANALYSIS_FEW_SHOT_EXAMPLES)
        messages.extend(EMERGENCY_DETECTION_EXAMPLES)
        
        # Add conversation history
        for msg in agent_input.conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        
        # Add current message
        messages.append({"role": "user", "content": agent_input.message})
        
        return messages

    def _parse_result(
        self,
        response_content: str,
        session_id: str,
        latency_ms: int,
        usage: Any,
    ) -> SymptomAnalysisResult:
        """Parse the agent response into structured output."""
        try:
            # Try to extract JSON from response
            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                parsed = json.loads(json_str)
                
                return SymptomAnalysisResult(
                    agent_name=self.agent_name,
                    session_id=session_id,
                    response_text=response_content,
                    differential_diagnoses=parsed.get("differential_diagnoses", []),
                    urgency_score=parsed.get("urgency_score", 5),
                    recommended_action=parsed.get("recommended_action", ""),
                    recommended_specialist=parsed.get("recommended_specialist"),
                    confidence=parsed.get("confidence", 0.7),
                    sources=[
                        SourceCitation(
                            source=src.get("source", "Medical Knowledge Base"),
                            document_type="clinical_guidelines",
                            relevance_score=0.8,
                        )
                        for src in parsed.get("sources", [])
                    ],
                    usage={
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    },
                    latency_ms=latency_ms,
                )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "voice_symptom_analyst_parse_failed",
                error=str(e),
                session_id=session_id,
            )

        # Fallback: return basic result
        return SymptomAnalysisResult(
            agent_name=self.agent_name,
            session_id=session_id,
            response_text=response_content,
            differential_diagnoses=[],
            urgency_score=5,
            recommended_action="Please consult with a healthcare professional for proper evaluation.",
            confidence=0.5,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            latency_ms=latency_ms,
        )
