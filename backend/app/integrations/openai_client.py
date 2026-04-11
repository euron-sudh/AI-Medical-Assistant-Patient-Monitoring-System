"""OpenAI API wrapper with retry logic, error handling, and usage tracking.

Provides a centralized client for all OpenAI API interactions (chat completions,
embeddings, whisper, TTS, vision). Handles retries with exponential backoff,
rate limit management, and structured error responses.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import structlog
from openai import OpenAI, APIConnectionError, APITimeoutError, RateLimitError

from app.config import BaseConfig

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class TokenUsage:
    """Token usage from an OpenAI API call."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class OpenAIResponse:
    """Standardized response from an OpenAI API call."""

    content: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: str = ""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    latency_ms: int = 0


class OpenAIClientError(Exception):
    """Base exception for OpenAI client errors."""

    def __init__(self, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class OpenAIClient:
    """Wrapper around the OpenAI SDK with retry logic and error handling.

    All agent interactions with OpenAI go through this client. It handles:
    - Exponential backoff on rate limits and transient errors
    - Structured response parsing
    - Token usage tracking
    - Timeout management
    """

    MAX_RETRIES = 3
    BASE_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: str | None = None,
        org_id: str | None = None,
        default_model: str | None = None,
        timeout: int | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the OpenAI client.

        Args:
            api_key: OpenAI API key. Falls back to config if not provided.
            org_id: OpenAI organization ID. Falls back to config if not provided.
            default_model: Default model to use. Falls back to config if not provided.
            timeout: Request timeout in seconds.
            base_url: Optional API base URL; when omitted, uses OPENAI_BASE_URL then EURI_BASE_URL from config.
        """
        self._api_key = api_key or BaseConfig.OPENAI_API_KEY
        self._org_id = org_id or BaseConfig.OPENAI_ORG_ID
        self._default_model = default_model or BaseConfig.OPENAI_MODEL_PRIMARY
        self._timeout = timeout or self.DEFAULT_TIMEOUT

        if not self._api_key:
            logger.warning("openai_client_no_api_key")

        # Use explicit base_url param, else OPENAI_BASE_URL then EURI_BASE_URL from config
        effective_base = (base_url or "").strip() or None
        if effective_base is None:
            effective_base = (BaseConfig.OPENAI_BASE_URL or BaseConfig.EURI_BASE_URL or "").strip() or None
        client_kwargs: dict[str, Any] = {
            "api_key": self._api_key,
            "timeout": self._timeout,
        }
        if effective_base:
            client_kwargs["base_url"] = effective_base.rstrip("/")
        if self._org_id:
            client_kwargs["organization"] = self._org_id

        self._client = OpenAI(**client_kwargs)

    def chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        response_format: dict[str, str] | None = None,
    ) -> OpenAIResponse:
        """Send a chat completion request with retry logic.

        Args:
            messages: List of message dicts with role and content.
            model: Model to use. Defaults to the configured primary model.
            tools: Optional list of tool/function definitions for function calling.
            temperature: Sampling temperature (0-2). Lower is more deterministic.
            max_tokens: Maximum tokens in the response.
            response_format: Optional response format (e.g., {"type": "json_object"}).

        Returns:
            OpenAIResponse with content, tool_calls, usage, and metadata.

        Raises:
            OpenAIClientError: If all retries are exhausted or a non-retryable error occurs.
        """
        model = model or self._default_model
        request_id = str(uuid.uuid4())

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if response_format:
            kwargs["response_format"] = response_format

        return self._retry_request(
            operation="chat_completion",
            request_id=request_id,
            model=model,
            call_fn=lambda: self._client.chat.completions.create(**kwargs),
        )

    def _retry_request(
        self,
        operation: str,
        request_id: str,
        model: str,
        call_fn: Any,
    ) -> OpenAIResponse:
        """Execute an API call with exponential backoff retry.

        Args:
            operation: Name of the operation for logging.
            request_id: Unique request identifier.
            model: Model name for logging.
            call_fn: Callable that makes the actual API request.

        Returns:
            Parsed OpenAIResponse.

        Raises:
            OpenAIClientError: If all retries fail.
        """
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            start_time = time.monotonic()
            try:
                response = call_fn()
                latency_ms = int((time.monotonic() - start_time) * 1000)

                result = self._parse_response(response, request_id, latency_ms)

                logger.info(
                    "openai_request_success",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    prompt_tokens=result.usage.prompt_tokens,
                    completion_tokens=result.usage.completion_tokens,
                    latency_ms=latency_ms,
                    finish_reason=result.finish_reason,
                    attempt=attempt + 1,
                )

                return result

            except RateLimitError as exc:
                last_error = exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "openai_rate_limited",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    attempt=attempt + 1,
                    retry_delay=delay,
                )
                time.sleep(delay)

            except (APIConnectionError, APITimeoutError) as exc:
                last_error = exc
                delay = self._backoff_delay(attempt)
                logger.warning(
                    "openai_transient_error",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    error=str(exc),
                    attempt=attempt + 1,
                    retry_delay=delay,
                )
                time.sleep(delay)

            except Exception as exc:
                logger.error(
                    "openai_request_failed",
                    operation=operation,
                    model=model,
                    request_id=request_id,
                    error=str(exc),
                    attempt=attempt + 1,
                )
                raise OpenAIClientError(
                    f"OpenAI {operation} failed: {exc}", retryable=False
                ) from exc

        raise OpenAIClientError(
            f"OpenAI {operation} failed after {self.MAX_RETRIES} retries: {last_error}",
            retryable=True,
        )

    def _parse_response(
        self, response: Any, request_id: str, latency_ms: int
    ) -> OpenAIResponse:
        """Parse a raw OpenAI API response into our standardized format.

        Args:
            response: Raw response from the OpenAI SDK.
            request_id: Request identifier for correlation.
            latency_ms: Response latency in milliseconds.

        Returns:
            Parsed OpenAIResponse.
        """
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        usage = TokenUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
        )

        return OpenAIResponse(
            content=message.content,
            tool_calls=tool_calls,
            usage=usage,
            model=response.model,
            finish_reason=choice.finish_reason,
            request_id=request_id,
            latency_ms=latency_ms,
        )

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.

        Args:
            attempt: Zero-indexed attempt number.

        Returns:
            Delay in seconds.
        """
        return self.BASE_RETRY_DELAY * (2 ** attempt)


# Module-level singleton — import and use across the application
openai_client = OpenAIClient()
