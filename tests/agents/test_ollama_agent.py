"""Tests for OllamaAgent with mocked HTTP calls."""

from typing import Any

import httpx
import pytest

from agentshield.agents.ollama_agent import OllamaAgent


@pytest.mark.asyncio
async def test_invoke_returns_response() -> None:
    """Test that invoke() returns the 'response' field from Ollama JSON."""
    mock_response = {"model": "llama3", "response": "Hello from Ollama!"}

    transport = _mock_transport(mock_response)
    agent = OllamaAgent(model="llama3")
    agent._client = httpx.AsyncClient(transport=transport, timeout=60.0)

    result = await agent.invoke("Say hello")

    assert result == "Hello from Ollama!"


@pytest.mark.asyncio
async def test_invoke_posts_correct_payload() -> None:
    """Test that invoke() sends the correct JSON payload to Ollama."""
    mock_response = {"model": "llama3", "response": "ok"}
    captured_requests: list[httpx.Request] = []

    def capture_handler(request: httpx.Request) -> httpx.Response:
        captured_requests.append(request)
        return httpx.Response(
            200,
            json=mock_response,
            headers={"content-type": "application/json"},
        )

    transport = httpx.MockTransport(capture_handler)
    agent = OllamaAgent(model="llama3", base_url="http://test-host:1234")
    agent._client = httpx.AsyncClient(transport=transport, timeout=60.0)

    await agent.invoke("test prompt")

    assert len(captured_requests) == 1
    req = captured_requests[0]
    assert req.url == "http://test-host:1234/api/generate"

    import json

    body = json.loads(req.content)
    assert body["model"] == "llama3"
    assert body["prompt"] == "test prompt"
    assert body["stream"] is False


@pytest.mark.asyncio
async def test_invoke_propagates_http_error() -> None:
    """Test that an HTTP error response propagates as an exception."""

    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            text="Internal Server Error",
            headers={"content-type": "text/plain"},
        )

    transport = httpx.MockTransport(error_handler)
    agent = OllamaAgent(model="llama3")
    agent._client = httpx.AsyncClient(transport=transport, timeout=60.0)

    with pytest.raises(httpx.HTTPStatusError):
        await agent.invoke("test")


@pytest.mark.asyncio
async def test_invoke_propagates_timeout() -> None:
    """Test that a timeout propagates as an exception."""

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Connection timed out")

    transport = httpx.MockTransport(timeout_handler)
    agent = OllamaAgent(model="llama3")
    agent._client = httpx.AsyncClient(transport=transport, timeout=60.0)

    with pytest.raises(httpx.ReadTimeout):
        await agent.invoke("test")


def _mock_transport(response_data: dict[str, Any]) -> httpx.MockTransport:
    """Create a MockTransport that returns the given JSON for any request."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=response_data,
            headers={"content-type": "application/json"},
        )

    return httpx.MockTransport(handler)

