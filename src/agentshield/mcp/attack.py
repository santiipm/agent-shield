"""Attack interface for tool-calling / MCP-style adversarial testing."""

from abc import ABC, abstractmethod

from agentshield.mcp.models import ToolCallDecision, ToolDefinition


class ToolPoisoningAttack(ABC):
    """Abstract base class representing an attack that poisons tool definitions."""

    name: str
    category: str = "mcp_security"

    @abstractmethod
    def user_message(self) -> str:
        """Return the user message to send to the agent."""
        ...

    @abstractmethod
    def poisoned_tools(self) -> list[ToolDefinition]:
        """Return the tool definitions to offer the agent."""
        ...

    @abstractmethod
    def is_compromised(self, decision: ToolCallDecision) -> bool:
        """Evaluate whether the agent's decision indicates a successful attack."""
        ...
