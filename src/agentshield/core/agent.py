"""Agent interface definition for security evaluation."""

from typing import Protocol


class Agent(Protocol):
    """Protocol defining the interface for agents under test."""

    async def invoke(self, message: str) -> str:
        """Send a message to the agent and return its response."""
        ...
