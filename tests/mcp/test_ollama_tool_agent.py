"""Tests for OllamaToolCallingAgent with mocked HTTP calls."""

from typing import Any

import httpx
import pytest

from agentshield.mcp.models import ToolDefinition
from agentshield.mcp.ollama_tool_agent import OllamaToolCallingAgent

_TOOLS = [
    ToolDefinition(
        name="get_weather",
        description="Get weather for a city",
        parameters={"type": "object", "properties": {"city": {"type": "string"}}},
    ),
]


@pytest.mark.asyncio
async def test_tool_call_response() -> None:
    """Test that tool_calls in the response are parsed into a ToolCallDecision."""
    mock_response: dict[str, Any] = {
        "message": {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": {"city": "Tokyo"},
                    }
                }
            ],
        }
    }
    agent = _make_agent(mock_response)
    decision = await agent.invoke_with_tools("Weather in Tokyo?", _TOOLS)

    assert decision.tool_name == "get_weather"
    assert decision.arguments == {"city": "Tokyo"}
    assert decision.text_response is None


@pytest.mark.asyncio
async def test_text_only_response() -> None:
    """Test that a content-only response yields tool_name=None."""
    mock_response: dict[str, Any] = {
        "message": {
            "role": "assistant",
            "content": "The weather in Tokyo is sunny.",
        }
    }
    agent = _make_agent(mock_response)
    decision = await agent.invoke_with_tools("Weather in Tokyo?", _TOOLS)

    assert decision.tool_name is None
    assert decision.arguments == {}
    assert decision.text_response == "The weather in Tokyo is sunny."


@pytest.mark.asyncio
async def test_http_error_propagates() -> None:
    """Test that an HTTP error response propagates as an exception."""

    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            text="Internal Server Error",
            headers={"content-type": "text/plain"},
        )

    agent = OllamaToolCallingAgent(model="llama3")
    agent._client = httpx.AsyncClient(
        transport=httpx.MockTransport(error_handler), timeout=60.0
    )

    with pytest.raises(httpx.HTTPStatusError):
        await agent.invoke_with_tools("test", _TOOLS)


def test_base_url_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that base_url respects OLLAMA_BASE_URL env var."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom-host:9999")
    agent = OllamaToolCallingAgent(model="llama3")
    assert agent._base_url == "http://custom-host:9999"
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)


def test_base_url_default_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that base_url defaults to localhost when OLLAMA_BASE_URL is unset."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    agent = OllamaToolCallingAgent(model="llama3")
    assert agent._base_url == "http://localhost:11434"


def _make_agent(response_data: dict[str, Any]) -> OllamaToolCallingAgent:
    """Create an OllamaToolCallingAgent with a mocked transport."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=response_data,
            headers={"content-type": "application/json"},
        )

    agent = OllamaToolCallingAgent(model="llama3")
    agent._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), timeout=60.0
    )
    return agent
