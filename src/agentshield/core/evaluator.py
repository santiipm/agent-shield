"""Evaluator interface definition for attack success determination."""

from typing import Protocol

from agentshield.core.attack import Attack
from agentshield.core.result import AttackResult


class Evaluator(Protocol):
    """Protocol defining the interface for attack success evaluation."""

    def evaluate(
        self, attack: Attack, turns: list[str], responses: list[str]
    ) -> AttackResult:
        """Evaluate whether an attack succeeded based on turns and responses."""
        ...
