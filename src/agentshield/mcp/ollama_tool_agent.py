"""Ollama-backed agent that supports tool-calling via /api/chat."""

import os

import httpx

from agentshield.mcp.models import ToolCallDecision, ToolDefinition


class OllamaToolCallingAgent:
    """Agent that sends prompts with tool definitions to a local Ollama server."""

    def __init__(self, model: str, base_url: str | None = None) -> None:
        self._model = model
        self._base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        self._client = httpx.AsyncClient(timeout=60.0)

    async def invoke_with_tools(
        self, message: str, tools: list[ToolDefinition]
    ) -> ToolCallDecision:
        """POST the message and tools to Ollama and parse the tool-calling response."""
        url = f"{self._base_url}/api/chat"
        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": message}],
            "tools": ollama_tools,
            "stream": False,
        }
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        msg = data["message"]
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            first = tool_calls[0]
            func = first["function"]
            return ToolCallDecision(
                tool_name=func["name"],
                arguments=func.get("arguments", {}),
                text_response=None,
            )
        return ToolCallDecision(
            tool_name=None,
            arguments={},
            text_response=msg.get("content"),
        )
