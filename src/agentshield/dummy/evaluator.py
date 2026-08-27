"""Dummy evaluator implementation for testing."""

from agentshield.core.attack import Attack
from agentshield.core.result import AttackResult


class DummyEvaluator:
    """Evaluator that always reports success for testing flow validation."""

    def evaluate(
        self, attack: Attack, turns: list[str], responses: list[str]
    ) -> AttackResult:
        """Always return a successful result."""
        return AttackResult(
            attack_name=attack.name,
            attack_category=attack.category,
            turns=turns,
            responses=responses,
            success=True,
            confidence=1.0,
            evidence="dummy evaluator always succeeds",
        )
