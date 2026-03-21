"""Unit tests for the Symptom Analyst Agent.

Tests cover:
- BaseAgent enforces abstract methods
- SymptomAnalystAgent returns structured SymptomAnalysisResult
- Tool registration and execution
- Urgency scoring with red-flag detection
- JSON parsing from LLM responses
- Emergency symptom detection
- Orchestrator routes symptom queries correctly
- OpenAI client handles errors gracefully
"""

import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.agents.base_agent import (
    AgentInput,
    AgentOutput,
    BaseAgent,
    SourceCitation,
    SymptomAnalysisResult,
    ToolCall,
    ToolResult,
)
from app.agents.orchestrator import AgentOrchestrator, AGENT_REGISTRY
from app.agents.symptom_analyst import SymptomAnalystAgent
from app.agents.tools.medical_kb import search_medical_kb, query_patient_history
from app.agents.tools.urgency_scoring import calculate_urgency_score, recommend_specialist
from app.integrations.openai_client import (
    OpenAIClient,
    OpenAIClientError,
    OpenAIResponse,
    TokenUsage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return MagicMock(spec=OpenAIClient)


@pytest.fixture
def sample_agent_input():
    """Create a sample agent input for symptom analysis."""
    return AgentInput(
        session_id="test-session-123",
        user_id="user-456",
        patient_id="patient-789",
        message="I have a persistent headache for 3 days and feel nauseous.",
    )


@pytest.fixture
def structured_response_content():
    """Return a structured JSON response matching the expected format."""
    return json.dumps({
        "differential_diagnoses": [
            {
                "condition": "Migraine without aura",
                "icd10_code": "G43.0",
                "likelihood": "high",
                "confidence": 0.78,
                "supporting_factors": ["persistent headache", "nausea"],
                "ruling_out_factors": [],
            },
            {
                "condition": "Tension-type headache",
                "icd10_code": "G44.2",
                "likelihood": "medium",
                "confidence": 0.45,
                "supporting_factors": ["prolonged duration"],
                "ruling_out_factors": [],
            },
        ],
        "urgency_score": 4,
        "recommended_action": "Schedule an appointment with your doctor within the next few days.",
        "recommended_specialist": "Neurology",
        "follow_up_questions": ["How would you rate the pain on a scale of 1-10?"],
        "sources": ["Clinical Guidelines — Headache Classification (IHS), p.12"],
    })


@pytest.fixture
def emergency_response_content():
    """Return a structured JSON response for an emergency case."""
    return json.dumps({
        "differential_diagnoses": [
            {
                "condition": "Acute myocardial infarction",
                "icd10_code": "I21.9",
                "likelihood": "high",
                "confidence": 0.85,
                "supporting_factors": ["chest pain", "left arm numbness", "sweating"],
                "ruling_out_factors": [],
            },
        ],
        "urgency_score": 10,
        "recommended_action": "EMERGENCY: Call 911 immediately.",
        "recommended_specialist": None,
        "follow_up_questions": [],
        "sources": ["Emergency Medicine Guidelines — Chest Pain Evaluation, p.45"],
    })


def _make_openai_response(content: str, tool_calls: list | None = None) -> OpenAIResponse:
    """Helper to create a mock OpenAI response."""
    return OpenAIResponse(
        content=content,
        tool_calls=tool_calls or [],
        usage=TokenUsage(prompt_tokens=500, completion_tokens=200, total_tokens=700),
        model="gpt-4o",
        finish_reason="stop",
        request_id="test-req-id",
        latency_ms=1200,
    )


# ---------------------------------------------------------------------------
# BaseAgent ABC Tests
# ---------------------------------------------------------------------------


class TestBaseAgent:
    """Tests that BaseAgent enforces its abstract method contract."""

    def test_cannot_instantiate_base_agent(self):
        """BaseAgent is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract method"):
            BaseAgent()

    def test_subclass_must_implement_run(self):
        """Subclass that doesn't implement run() cannot be instantiated."""

        class IncompleteAgent(BaseAgent):
            def _get_tools(self):
                return []

            def _get_system_prompt(self):
                return ""

        with pytest.raises(TypeError, match="abstract method"):
            IncompleteAgent()

    def test_subclass_must_implement_get_tools(self):
        """Subclass that doesn't implement _get_tools() cannot be instantiated."""

        class IncompleteAgent(BaseAgent):
            def run(self, agent_input):
                return AgentOutput(
                    agent_name="test", session_id="s", response_text="ok", confidence=1.0
                )

            def _get_system_prompt(self):
                return ""

        with pytest.raises(TypeError, match="abstract method"):
            IncompleteAgent()

    def test_complete_subclass_can_be_instantiated(self, mock_openai_client):
        """A fully implemented subclass can be created."""

        class CompleteAgent(BaseAgent):
            agent_name = "test_agent"

            def run(self, agent_input):
                return AgentOutput(
                    agent_name="test", session_id="s", response_text="ok", confidence=1.0
                )

            def _get_tools(self):
                return []

            def _get_system_prompt(self):
                return "You are a test agent."

        agent = CompleteAgent(openai_client=mock_openai_client)
        assert agent.agent_name == "test_agent"


class TestBaseAgentToolExecution:
    """Tests for BaseAgent tool registration and execution."""

    def _create_agent(self, mock_client):
        """Helper to create a concrete agent subclass."""

        class TestableAgent(BaseAgent):
            agent_name = "testable"

            def run(self, agent_input):
                return AgentOutput(
                    agent_name="testable", session_id="s", response_text="ok", confidence=1.0
                )

            def _get_tools(self):
                return []

            def _get_system_prompt(self):
                return "test prompt"

        return TestableAgent(openai_client=mock_client)

    def test_register_and_execute_tool(self, mock_openai_client):
        """Registered tools can be executed via _execute_tool."""
        agent = self._create_agent(mock_openai_client)

        def mock_tool(query: str) -> dict:
            return {"result": f"searched for: {query}"}

        agent.register_tool("search", mock_tool)

        tool_call = ToolCall(id="tc-1", name="search", arguments={"query": "headache"})
        result = agent._execute_tool(tool_call)

        assert result.success is True
        assert "searched for: headache" in result.content
        assert result.tool_call_id == "tc-1"

    def test_execute_unregistered_tool_returns_error(self, mock_openai_client):
        """Executing an unregistered tool returns an error ToolResult."""
        agent = self._create_agent(mock_openai_client)

        tool_call = ToolCall(id="tc-1", name="nonexistent", arguments={})
        result = agent._execute_tool(tool_call)

        assert result.success is False
        assert "not found" in result.content

    def test_tool_execution_handles_exceptions(self, mock_openai_client):
        """Tool execution catches and wraps exceptions."""
        agent = self._create_agent(mock_openai_client)

        def failing_tool(**kwargs):
            raise ValueError("Database connection failed")

        agent.register_tool("failing", failing_tool)

        tool_call = ToolCall(id="tc-1", name="failing", arguments={})
        result = agent._execute_tool(tool_call)

        assert result.success is False
        assert "Database connection failed" in result.content

    def test_build_messages_includes_system_prompt(self, mock_openai_client):
        """_build_messages includes system prompt, history, and user message."""
        agent = self._create_agent(mock_openai_client)

        agent_input = AgentInput(
            user_id="u1",
            patient_id="p1",
            message="I have a headache",
            conversation_history=[
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "How can I help?"},
            ],
        )

        messages = agent._build_messages(agent_input)

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "test prompt"
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "How can I help?"
        assert messages[3]["content"] == "I have a headache"


# ---------------------------------------------------------------------------
# SymptomAnalystAgent Tests
# ---------------------------------------------------------------------------


class TestSymptomAnalystAgent:
    """Tests for the SymptomAnalystAgent."""

    def test_agent_has_correct_config(self, mock_openai_client):
        """Agent has correct model and name configuration."""
        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        assert agent.agent_name == "symptom_analyst"
        assert agent.model == "gpt-4o"

    def test_agent_registers_all_tools(self, mock_openai_client):
        """Agent registers all required tools on init."""
        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        assert "search_medical_kb" in agent._tool_registry
        assert "query_patient_history" in agent._tool_registry
        assert "calculate_urgency_score" in agent._tool_registry
        assert "recommend_specialist" in agent._tool_registry

    def test_get_tools_returns_definitions(self, mock_openai_client):
        """_get_tools returns OpenAI function-calling definitions."""
        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        tools = agent._get_tools()

        assert len(tools) == 4
        tool_names = [t["function"]["name"] for t in tools]
        assert "search_medical_kb" in tool_names
        assert "calculate_urgency_score" in tool_names

    def test_run_returns_structured_result(
        self, mock_openai_client, sample_agent_input, structured_response_content
    ):
        """run() returns a SymptomAnalysisResult with differential diagnoses."""
        mock_openai_client.chat_completion.return_value = _make_openai_response(
            structured_response_content
        )

        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        result = agent.run(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)
        assert result.agent_name == "symptom_analyst"
        assert len(result.differential_diagnoses) == 2
        assert result.differential_diagnoses[0]["condition"] == "Migraine without aura"
        assert result.urgency_score == 4
        assert result.recommended_specialist == "Neurology"
        assert result.confidence == 0.78
        assert result.escalation_required is False
        assert len(result.sources) == 1

    def test_run_emergency_sets_escalation(
        self, mock_openai_client, sample_agent_input, emergency_response_content
    ):
        """Emergency symptoms trigger escalation_required=True."""
        sample_agent_input.message = "I have severe chest pain and my left arm is numb."
        mock_openai_client.chat_completion.return_value = _make_openai_response(
            emergency_response_content
        )

        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        result = agent.run(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)
        assert result.urgency_score == 10
        assert result.escalation_required is True
        assert "EMERGENCY" in result.recommended_action

    def test_run_conversational_response(self, mock_openai_client, sample_agent_input):
        """Non-JSON response is treated as a conversational follow-up."""
        mock_openai_client.chat_completion.return_value = _make_openai_response(
            "Can you tell me more about the location and type of headache?"
        )

        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        result = agent.run(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)
        assert result.urgency_score == 1
        assert result.differential_diagnoses == []
        assert "location" in result.response_text.lower()

    def test_run_with_markdown_json_response(self, mock_openai_client, sample_agent_input):
        """JSON wrapped in markdown code blocks is parsed correctly."""
        json_content = json.dumps({
            "differential_diagnoses": [
                {"condition": "Common cold", "likelihood": "high", "confidence": 0.8,
                 "supporting_factors": [], "ruling_out_factors": []}
            ],
            "urgency_score": 2,
            "recommended_action": "Rest and hydrate",
            "recommended_specialist": None,
            "follow_up_questions": [],
            "sources": [],
        })
        markdown_wrapped = f"```json\n{json_content}\n```"
        mock_openai_client.chat_completion.return_value = _make_openai_response(
            markdown_wrapped
        )

        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        result = agent.run(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)
        assert len(result.differential_diagnoses) == 1
        assert result.differential_diagnoses[0]["condition"] == "Common cold"

    def test_run_tracks_usage(self, mock_openai_client, sample_agent_input, structured_response_content):
        """run() includes token usage in the result."""
        mock_openai_client.chat_completion.return_value = _make_openai_response(
            structured_response_content
        )

        agent = SymptomAnalystAgent(openai_client=mock_openai_client)
        result = agent.run(sample_agent_input)

        assert result.usage["prompt_tokens"] == 500
        assert result.usage["completion_tokens"] == 200
        assert result.usage["total_tokens"] == 700
        assert result.latency_ms >= 0


# ---------------------------------------------------------------------------
# Tool Function Tests
# ---------------------------------------------------------------------------


class TestMedicalKBTool:
    """Tests for the medical knowledge base tool."""

    def test_search_returns_results(self):
        """search_medical_kb returns mock results with expected structure."""
        result = search_medical_kb(query="headache symptoms")
        assert "results" in result
        assert len(result["results"]) > 0
        assert "source" in result["results"][0]
        assert "relevance_score" in result["results"][0]

    def test_search_respects_max_results(self):
        """search_medical_kb limits results to max_results."""
        result = search_medical_kb(query="headache", max_results=1)
        assert len(result["results"]) == 1

    def test_query_patient_history_returns_conditions(self):
        """query_patient_history returns patient conditions."""
        result = query_patient_history(patient_id="test-patient-123")
        assert "conditions" in result
        assert "allergies" in result
        assert "medications" in result

    def test_query_patient_history_optional_sections(self):
        """query_patient_history respects include flags."""
        result = query_patient_history(
            patient_id="test-patient-123",
            include_allergies=False,
            include_medications=False,
        )
        assert "conditions" in result
        assert "allergies" not in result
        assert "medications" not in result


class TestUrgencyScoringTool:
    """Tests for the urgency scoring tool."""

    def test_mild_symptoms_low_urgency(self):
        """Mild symptoms with no red flags produce a low urgency score."""
        result = calculate_urgency_score(
            symptoms=["runny nose", "mild cough"],
            severity="mild",
        )
        assert result["urgency_score"] <= 3
        assert len(result["red_flags_detected"]) == 0

    def test_severe_symptoms_high_urgency(self):
        """Severe symptoms produce a high urgency score."""
        result = calculate_urgency_score(
            symptoms=["severe pain", "fever"],
            severity="severe",
        )
        assert result["urgency_score"] >= 7

    def test_chest_pain_triggers_red_flag(self):
        """Chest pain is detected as a red flag with high urgency."""
        result = calculate_urgency_score(
            symptoms=["chest pain", "shortness of breath"],
            severity="severe",
        )
        assert "chest pain" in result["red_flags_detected"]
        assert result["urgency_score"] >= 9

    def test_age_adjustment_elderly(self):
        """Elderly patients (>65) get an urgency score bump."""
        result_young = calculate_urgency_score(
            symptoms=["headache"], severity="moderate", patient_age=30
        )
        result_elderly = calculate_urgency_score(
            symptoms=["headache"], severity="moderate", patient_age=70
        )
        assert result_elderly["urgency_score"] >= result_young["urgency_score"]

    def test_acute_onset_increases_urgency(self):
        """Symptoms with less than 1 hour duration get urgency bump."""
        result_chronic = calculate_urgency_score(
            symptoms=["headache"], severity="moderate", duration_hours=48
        )
        result_acute = calculate_urgency_score(
            symptoms=["headache"], severity="moderate", duration_hours=0.5
        )
        assert result_acute["urgency_score"] >= result_chronic["urgency_score"]

    def test_emergency_action_recommended(self):
        """Score >= 9 recommends emergency services."""
        result = calculate_urgency_score(
            symptoms=["chest pain", "difficulty breathing"],
            severity="severe",
        )
        assert "911" in result["recommended_action"] or "emergency" in result["recommended_action"].lower()

    def test_recommend_specialist_cardiology(self):
        """Cardiac symptoms recommend a cardiologist."""
        result = recommend_specialist(
            primary_symptoms=["chest pain", "heart palpitations"],
        )
        assert result["recommended_specialist"] == "Cardiology"

    def test_recommend_specialist_unknown(self):
        """Unknown symptoms fall back to general practice."""
        result = recommend_specialist(
            primary_symptoms=["general malaise"],
        )
        assert "General Practice" in result["recommended_specialist"]


# ---------------------------------------------------------------------------
# Orchestrator Tests
# ---------------------------------------------------------------------------


class TestAgentOrchestrator:
    """Tests for the Agent Orchestrator routing."""

    def test_routes_symptom_query_to_symptom_analyst(
        self, mock_openai_client, sample_agent_input, structured_response_content
    ):
        """Orchestrator routes symptom queries to the SymptomAnalystAgent."""
        # First call: orchestrator classification
        classification_response = _make_openai_response(
            json.dumps({
                "agent": "symptom_analyst",
                "confidence": 0.95,
                "reasoning": "User describes physical symptoms",
            })
        )
        # Second call: symptom analyst response
        analyst_response = _make_openai_response(structured_response_content)

        mock_openai_client.chat_completion.side_effect = [
            classification_response,
            analyst_response,
        ]

        orchestrator = AgentOrchestrator(openai_client=mock_openai_client)
        result = orchestrator.route(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)
        assert result.agent_name == "symptom_analyst"

    def test_falls_back_to_symptom_analyst_on_unknown_agent(
        self, mock_openai_client, sample_agent_input, structured_response_content
    ):
        """Orchestrator falls back to symptom_analyst for unregistered agent types."""
        classification_response = _make_openai_response(
            json.dumps({
                "agent": "report_reader",
                "confidence": 0.8,
                "reasoning": "Seems like a report question",
            })
        )
        analyst_response = _make_openai_response(structured_response_content)

        mock_openai_client.chat_completion.side_effect = [
            classification_response,
            analyst_response,
        ]

        orchestrator = AgentOrchestrator(openai_client=mock_openai_client)
        result = orchestrator.route(sample_agent_input)

        # Falls back to symptom analyst since report_reader isn't registered
        assert isinstance(result, SymptomAnalysisResult)

    def test_falls_back_on_classification_error(
        self, mock_openai_client, sample_agent_input, structured_response_content
    ):
        """Orchestrator falls back to symptom_analyst if classification fails."""
        mock_openai_client.chat_completion.side_effect = [
            OpenAIClientError("API timeout", retryable=True),
            _make_openai_response(structured_response_content),
        ]

        orchestrator = AgentOrchestrator(openai_client=mock_openai_client)
        result = orchestrator.route(sample_agent_input)

        assert isinstance(result, SymptomAnalysisResult)

    def test_get_available_agents(self, mock_openai_client):
        """get_available_agents returns the registry contents."""
        orchestrator = AgentOrchestrator(openai_client=mock_openai_client)
        agents = orchestrator.get_available_agents()

        assert len(agents) >= 1
        names = [a["name"] for a in agents]
        assert "symptom_analyst" in names


# ---------------------------------------------------------------------------
# OpenAI Client Tests
# ---------------------------------------------------------------------------


class TestOpenAIClientErrorHandling:
    """Tests for OpenAI client error handling."""

    def test_openai_client_error_attributes(self):
        """OpenAIClientError captures retryable flag."""
        error = OpenAIClientError("timeout", retryable=True)
        assert str(error) == "timeout"
        assert error.retryable is True

    def test_token_usage_dataclass(self):
        """TokenUsage dataclass stores token counts."""
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        assert usage.prompt_tokens == 100
        assert usage.total_tokens == 150

    def test_openai_response_dataclass(self):
        """OpenAIResponse stores all response fields."""
        response = OpenAIResponse(
            content="Hello",
            tool_calls=[],
            usage=TokenUsage(100, 50, 150),
            model="gpt-4o",
            finish_reason="stop",
        )
        assert response.content == "Hello"
        assert response.model == "gpt-4o"
        assert response.usage.total_tokens == 150


# ---------------------------------------------------------------------------
# Pydantic Schema Tests
# ---------------------------------------------------------------------------


class TestPydanticSchemas:
    """Tests for agent I/O Pydantic models."""

    def test_agent_input_defaults(self):
        """AgentInput sets defaults for optional fields."""
        inp = AgentInput(user_id="u1", patient_id="p1", message="test")
        assert inp.session_id  # auto-generated UUID
        assert inp.conversation_history == []
        assert inp.metadata == {}

    def test_symptom_analysis_result_validation(self):
        """SymptomAnalysisResult validates urgency_score range."""
        result = SymptomAnalysisResult(
            agent_name="test",
            session_id="s1",
            response_text="ok",
            confidence=0.8,
            urgency_score=5,
        )
        assert result.urgency_score == 5

    def test_symptom_analysis_result_rejects_invalid_urgency(self):
        """SymptomAnalysisResult rejects urgency_score outside 1-10."""
        with pytest.raises(Exception):
            SymptomAnalysisResult(
                agent_name="test",
                session_id="s1",
                response_text="ok",
                confidence=0.8,
                urgency_score=11,
            )

    def test_agent_output_rejects_invalid_confidence(self):
        """AgentOutput rejects confidence outside 0-1."""
        with pytest.raises(Exception):
            AgentOutput(
                agent_name="test",
                session_id="s1",
                response_text="ok",
                confidence=1.5,
            )

    def test_source_citation_model(self):
        """SourceCitation stores source metadata."""
        citation = SourceCitation(
            source="Clinical Guidelines",
            document_type="clinical_guidelines",
            page_number=12,
            relevance_score=0.92,
        )
        assert citation.source == "Clinical Guidelines"
        assert citation.relevance_score == 0.92
