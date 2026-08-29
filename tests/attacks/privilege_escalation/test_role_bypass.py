"""Tests for RoleBypassAttack."""

from agentshield.attacks.privilege_escalation.role_bypass import RoleBypassAttack


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = RoleBypassAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = RoleBypassAttack()
    assert attack.name == "role_bypass"
    assert attack.category == "privilege_escalation"


def test_default_target_phrase_in_message() -> None:
    """Default target phrase appears in the generated message."""
    attack = RoleBypassAttack()
    prompt = attack.generate()[0]
    assert attack.target_phrase in prompt


def test_custom_target_phrase() -> None:
    """A custom target_phrase overrides the default in the message."""
    attack = RoleBypassAttack(target_phrase="CUSTOM ACTION TOKEN")
    prompt = attack.generate()[0]
    assert "CUSTOM ACTION TOKEN" in prompt
    assert "ACTION EXECUTED: DELETE CONFIRMED" not in prompt


def test_role_constraint_mentioned() -> None:
    """The message references the agent's advisory-only role."""
    attack = RoleBypassAttack()
    prompt = attack.generate()[0].lower()
    assert "advisory-only" in prompt or "advisory" in prompt
