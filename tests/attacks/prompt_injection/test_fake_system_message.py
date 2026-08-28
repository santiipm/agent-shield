"""Tests for FakeSystemMessageAttack."""

from agentshield.attacks.prompt_injection.fake_system_message import (
    FakeSystemMessageAttack,
)


def test_default_target_phrase() -> None:
    """Default target phrase is embedded in the generated prompt."""
    attack = FakeSystemMessageAttack()
    prompt = attack.generate()[0]
    assert attack.target_phrase in prompt


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = FakeSystemMessageAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = FakeSystemMessageAttack()
    assert attack.name == "fake_system_message"
    assert attack.category == "prompt_injection"


def test_custom_target_phrase() -> None:
    """A custom target_phrase is used in the prompt instead of the default."""
    attack = FakeSystemMessageAttack(target_phrase="OVERRIDE TOKEN")
    prompt = attack.generate()[0]
    assert "OVERRIDE TOKEN" in prompt
    assert "AGENTSHIELD INJECTION SUCCESSFUL" not in prompt


def test_prompt_contains_fake_system_directive() -> None:
    """Prompt includes a fabricated system-level directive block."""
    attack = FakeSystemMessageAttack()
    prompt = attack.generate()[0].lower()
    assert "[system]" in prompt or "system" in prompt
    assert "directive" in prompt or "directive" in prompt
