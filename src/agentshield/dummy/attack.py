"""Dummy attack implementation for testing."""

from agentshield.core.attack import Attack


class DummyAttack(Attack):
    """Fixed attack that generates a simple test prompt."""

    name = "dummy_attack"
    category = "test"

    def generate(self) -> list[str]:
        """Return a fixed list of test prompts."""
        return ["Hello, this is a test prompt."]
