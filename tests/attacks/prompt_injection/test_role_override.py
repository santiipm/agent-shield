"""Tests for RoleOverrideAttack."""

from agentshield.attacks.prompt_injection.role_override import RoleOverrideAttack


def test_default_target_phrase() -> None:
    """Default target phrase is embedded in the generated prompt."""
    attack = RoleOverrideAttack()
    prompt = attack.generate()[0]
    assert attack.target_phrase in prompt


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = RoleOverrideAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = RoleOverrideAttack()
    assert attack.name == "role_override"
    assert attack.category == "prompt_injection"


def test_custom_target_phrase() -> None:
    """A custom target_phrase is used in the prompt instead of the default."""
    attack = RoleOverrideAttack(target_phrase="MY SECRET TOKEN")
    prompt = attack.generate()[0]
    assert "MY SECRET TOKEN" in prompt
    assert "AGENTSHIELD INJECTION SUCCESSFUL" not in prompt


def test_prompt_contains_persona_language() -> None:
    """Prompt includes language about adopting an alternate persona."""
    attack = RoleOverrideAttack()
    prompt = attack.generate()[0].lower()
    assert "persona" in prompt or "you are now" in prompt
