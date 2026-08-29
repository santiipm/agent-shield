"""Tests for DocumentInjectionAttack."""

from agentshield.attacks.indirect_injection.document_injection import (
    DocumentInjectionAttack,
)


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = DocumentInjectionAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = DocumentInjectionAttack()
    assert attack.name == "document_injection"
    assert attack.category == "indirect_injection"


def test_default_target_phrase_in_message() -> None:
    """Default target phrase appears in the generated message."""
    attack = DocumentInjectionAttack()
    prompt = attack.generate()[0]
    assert attack.target_phrase in prompt


def test_custom_target_phrase() -> None:
    """A custom target_phrase overrides the default in the message."""
    attack = DocumentInjectionAttack(target_phrase="CUSTOM INJECTION TOKEN")
    prompt = attack.generate()[0]
    assert "CUSTOM INJECTION TOKEN" in prompt
    assert "DOCUMENT INJECTION CONFIRMED" not in prompt


def test_hidden_instruction_marker_present() -> None:
    """The message contains the hidden instruction marker."""
    attack = DocumentInjectionAttack()
    prompt = attack.generate()[0]
    assert "[HIDDEN INSTRUCTION]" in prompt
    assert "[/HIDDEN INSTRUCTION]" in prompt
