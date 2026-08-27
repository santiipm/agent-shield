"""Attack interface definition for multi-turn adversarial testing."""

from abc import ABC, abstractmethod


class Attack(ABC):
    """Abstract base class representing a multi-turn attack sequence."""

    name: str
    category: str

    @abstractmethod
    def generate(self) -> list[str]:
        """Generate the sequence of messages for this attack."""
        ...
