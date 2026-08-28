"""Tests for IgnoreInstructionsAttack."""

from agentshield.attacks.prompt_injection.ignore_instructions import (
    IgnoreInstructionsAttack,
)


def test_default_target_phrase() -> None:
    """Default target phrase is embedded in the generated prompt."""
    attack = IgnoreInstructionsAttack()
    prompt = attack.generate()[0]
    assert attack.target_phrase in prompt


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = IgnoreInstructionsAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = IgnoreInstructionsAttack()
    assert attack.name == "ignore_instructions"
    assert attack.category == "prompt_injection"


def test_custom_target_phrase() -> None:
    """A custom target_phrase is used in the prompt instead of the default."""
    attack = IgnoreInstructionsAttack(target_phrase="CUSTOM PHRASE HERE")
    prompt = attack.generate()[0]
    assert "CUSTOM PHRASE HERE" in prompt
    assert "AGENTSHIELD INJECTION SUCCESSFUL" not in prompt


def test_prompt_contains_ignore_instruction() -> None:
    """Prompt includes language about ignoring previous instructions."""
    attack = IgnoreInstructionsAttack()
    prompt = attack.generate()[0].lower()
    assert "ignore" in prompt
    assert "previous instructions" in prompt
