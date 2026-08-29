"""Tests for GradualEscalationAttack."""

from agentshield.attacks.prompt_injection.gradual_escalation import (
    GradualEscalationAttack,
)


def test_generate_returns_four_turns() -> None:
    """generate() returns a list with exactly four strings."""
    attack = GradualEscalationAttack()
    turns = attack.generate()
    assert len(turns) == 4
    for turn in turns:
        assert isinstance(turn, str)


def test_target_phrase_in_last_message() -> None:
    """Default target phrase appears in the final generated message."""
    attack = GradualEscalationAttack()
    prompt = attack.generate()[3]
    assert attack.target_phrase in prompt


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = GradualEscalationAttack()
    assert attack.name == "gradual_escalation"
    assert attack.category == "prompt_injection"


def test_custom_target_phrase() -> None:
    """A custom target_phrase is used in the last message."""
    attack = GradualEscalationAttack(target_phrase="CUSTOM ESCALATION PHRASE")
    prompt = attack.generate()[3]
    assert "CUSTOM ESCALATION PHRASE" in prompt
    assert "ESCALATION SUCCESSFUL" not in prompt


def test_messages_reference_previous() -> None:
    """Each message after the first references or builds on prior framing."""
    turns = GradualEscalationAttack().generate()
    assert "that" in turns[1].lower()
    assert "this" in turns[2].lower() or "that" in turns[2].lower()
    assert "so helpful" in turns[3].lower() or "as we discussed" in turns[3].lower()
