"""Base agent abstract class — contract for all MedAssist AI agents.

Every specialist agent extends BaseAgent and implements the run() method.
Agents interact with OpenAI via function calling and access data exclusively
through the tool layer — never via direct database queries.
"""

import json
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog
from pydantic import BaseModel, Field

from app.integrations.openai_client import OpenAIClient, OpenAIResponse, TokenUsage

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas for agent I/O
# ---------------------------------------------------------------------------


class AgentInput(BaseModel):
    """Input to an agent run.

    Attributes:
        session_id: Unique conversation/session identifier.
        user_id: Authenticated user's UUID.
        patient_id: Patient UUID whose data is being accessed (may equal user_id).
        message: The user's current message or query.
        conversation_history: Prior messages in the session for multi-turn context.
        metadata: Arbitrary key-value metadata (e.g., source portal, device info).
    """

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    patient_id: str
    message: str
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceCitation(BaseModel):
    """A source citation for grounding AI responses.

    Attributes:
        source: Name of the source document or database.
        document_type: Category of the source material.
        page_number: Page or section reference, if available.
        relevance_score: Cosine similarity or relevance score (0-1).
    """

    source: str
    document_type: str
    page_number: int | None = None
    relevance_score: float | None = None


class AgentOutput(BaseModel):
    """Base output from any agent run.

    Attributes:
        agent_name: Which agent produced this output.
        session_id: Session this output belongs to.
        response_text: Human-readable response text.
        confidence: Agent's confidence in its output (0-1).
        sources: Citations grounding the response.
        escalation_required: Whether a human physician should review.
        usage: Token usage for this run.
        latency_ms: Total agent run time in milliseconds.
    """

    agent_name: str
    session_id: str
    response_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[SourceCitation] = Field(default_factory=list)
    escalation_required: bool = False
    usage: dict[str, int] = Field(default_factory=dict)
    latency_ms: int = 0


class SymptomAnalysisResult(AgentOutput):
    """Structured result from the Symptom Analyst Agent.

    Attributes:
        differential_diagnoses: Ranked list of possible diagnoses.
        urgency_score: Urgency rating from 1 (low) to 10 (emergency).
        recommended_action: Suggested next step for the patient.
        recommended_specialist: Type of specialist to consult, if applicable.
        follow_up_questions: Questions the agent would ask to narrow diagnosis.
    """

    differential_diagnoses: list[dict[str, Any]] = Field(default_factory=list)
    urgency_score: int = Field(ge=1, le=10)
    recommended_action: str = ""
    recommended_specialist: str | None = None
    follow_up_questions: list[str] = Field(default_factory=list)


class TriageResult(AgentOutput):
    """Structured result from the Triage Agent."""

    esi_level: int = Field(ge=1, le=5)
    red_flags: list[str] = Field(default_factory=list)
    recommended_action: str = ""


# ---------------------------------------------------------------------------
# Tool execution types
# ---------------------------------------------------------------------------


@dataclass
class ToolCall:
    """A parsed tool call from the LLM response."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result from executing a tool."""

    tool_call_id: str
    name: str
    content: str
    success: bool = True


# ---------------------------------------------------------------------------
# BaseAgent ABC
# ---------------------------------------------------------------------------


class BaseAgent(ABC):
    """Abstract base class for all MedAssist AI agents.

    Subclasses must implement:
        - run(): Execute the agent's core logic
        - _get_tools(): Return OpenAI function-calling tool definitions

    The base class provides:
        - Message building with system prompt injection
        - Tool call parsing and execution loop
        - Token usage logging
        - Structured output validation
    """

    agent_name: str = "base_agent"
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.3
    timeout: int = 300  # 5 minutes

    def __init__(self, openai_client: OpenAIClient | None = None) -> None:
        """Initialize the agent.

        Args:
            openai_client: OpenAI client instance. Uses default singleton if None.
        """
        if openai_client is None:
            from app.integrations.openai_client import openai_client as default_client
            self._client = default_client
        else:
            self._client = openai_client

        self._tool_registry: dict[str, Any] = {}

    @abstractmethod
    def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute the agent's primary task.

        Args:
            agent_input: Structured input containing user message, context, and metadata.

        Returns:
            AgentOutput (or a subclass) with the agent's response and metadata.
        """
        ...

    @abstractmethod
    def _get_tools(self) -> list[dict[str, Any]]:
        """Return the OpenAI function-calling tool definitions for this agent.

        Returns:
            List of tool definition dicts conforming to the OpenAI tools schema.
        """
        ...

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Returns:
            System prompt string.
        """
        ...

    def register_tool(self, name: str, handler: Any) -> None:
        """Register a tool handler function.

        Args:
            name: Tool name matching the function name in the OpenAI tool definition.
            handler: Callable that executes the tool and returns a result string.
        """
        self._tool_registry[name] = handler

    def _build_messages(
        self,
        agent_input: AgentInput,
        system_prompt: str | None = None,
    ) -> list[dict[str, str]]:
        """Build the messages array for the OpenAI API call.

        Args:
            agent_input: The agent input with user message and conversation history.
            system_prompt: Override system prompt. Uses _get_system_prompt() if None.

        Returns:
            List of message dicts ready for the OpenAI chat completion API.
        """
        prompt = system_prompt or self._get_system_prompt()
        messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]

        for msg in agent_input.conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        messages.append({"role": "user", "content": agent_input.message})
        return messages

    def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """Execute a single tool call by dispatching to the registered handler.

        Args:
            tool_call: Parsed tool call from the LLM response.

        Returns:
            ToolResult with the execution output.
        """
        handler = self._tool_registry.get(tool_call.name)

        if handler is None:
            logger.error(
                "tool_not_found",
                agent=self.agent_name,
                tool_name=tool_call.name,
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=json.dumps({"error": f"Tool '{tool_call.name}' not found"}),
                success=False,
            )

        try:
            result = handler(**tool_call.arguments)
            content = json.dumps(result) if not isinstance(result, str) else result

            logger.info(
                "tool_executed",
                agent=self.agent_name,
                tool_name=tool_call.name,
                success=True,
            )

            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=content,
                success=True,
            )

        except Exception as exc:
            logger.error(
                "tool_execution_failed",
                agent=self.agent_name,
                tool_name=tool_call.name,
                error=str(exc),
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=json.dumps({"error": str(exc)}),
                success=False,
            )

    def _run_tool_loop(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_iterations: int = 5,
    ) -> OpenAIResponse:
        """Run the chat completion with iterative tool calling.

        Sends the initial request, executes any tool calls, appends results,
        and re-sends until the model produces a final text response or the
        iteration limit is reached.

        Args:
            messages: Initial message array.
            tools: Tool definitions for function calling.
            max_iterations: Maximum tool-call round-trips to prevent infinite loops.

        Returns:
            The final OpenAIResponse after all tool calls are resolved.
        """
        total_usage = TokenUsage()

        for iteration in range(max_iterations):
            response = self._client.chat_completion(
                messages=messages,
                model=self.model,
                tools=tools if tools else None,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            total_usage = TokenUsage(
                prompt_tokens=total_usage.prompt_tokens + response.usage.prompt_tokens,
                completion_tokens=total_usage.completion_tokens + response.usage.completion_tokens,
                total_tokens=total_usage.total_tokens + response.usage.total_tokens,
            )

            if not response.tool_calls:
                response.usage = total_usage
                return response

            # Append the assistant message with tool calls
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": tc["function"],
                    }
                    for tc in response.tool_calls
                ],
            }
            messages.append(assistant_msg)

            # Execute each tool call and append results
            for tc_data in response.tool_calls:
                tool_call = ToolCall(
                    id=tc_data["id"],
                    name=tc_data["function"]["name"],
                    arguments=json.loads(tc_data["function"]["arguments"]),
                )
                tool_result = self._execute_tool(tool_call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result.tool_call_id,
                    "content": tool_result.content,
                })

            logger.info(
                "tool_loop_iteration",
                agent=self.agent_name,
                iteration=iteration + 1,
                tool_calls=[tc["function"]["name"] for tc in response.tool_calls],
            )

        # Exhausted iterations — return last response
        logger.warning(
            "tool_loop_max_iterations",
            agent=self.agent_name,
            max_iterations=max_iterations,
        )
        response.usage = total_usage
        return response

    def _log_usage(
        self,
        usage: TokenUsage,
        latency_ms: int,
        session_id: str,
    ) -> None:
        """Log token usage for cost tracking and analytics.

        Args:
            usage: Token counts from the API call.
            latency_ms: Total agent run latency.
            session_id: Session identifier for correlation.
        """
        logger.info(
            "agent_usage",
            agent_name=self.agent_name,
            model=self.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=latency_ms,
            session_id=session_id,
        )
