"""Agent interface for tool-calling evaluations."""

from typing import Protocol

from agentshield.mcp.models import ToolCallDecision, ToolDefinition


class ToolCallingAgent(Protocol):
    """Protocol defining the interface for agents that accept tool definitions."""

    async def invoke_with_tools(
        self, message: str, tools: list[ToolDefinition]
    ) -> ToolCallDecision:
        """Send a message along with available tools and return the agent's decision."""
        ...
