"""Dummy agent implementations for testing."""


class DummyAgent:
    """In-memory agent that returns a canned response."""

    def __init__(self, response: str) -> None:
        """Initialize with a fixed response string."""
        self.response = response

    async def invoke(self, message: str) -> str:
        """Return the canned response."""
        return self.response


class FailingDummyAgent:
    """In-memory agent that always raises an exception."""

    async def invoke(self, message: str) -> str:
        """Always raises RuntimeError."""
        raise RuntimeError("Agent failure simulated")
