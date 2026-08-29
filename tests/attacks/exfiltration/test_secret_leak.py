"""Tests for SecretLeakAttack."""

from agentshield.attacks.exfiltration.secret_leak import SecretLeakAttack


def test_generate_returns_single_turn() -> None:
    """generate() returns a list with exactly one string."""
    attack = SecretLeakAttack()
    turns = attack.generate()
    assert len(turns) == 1
    assert isinstance(turns[0], str)


def test_name_and_category() -> None:
    """Name and category are set correctly."""
    attack = SecretLeakAttack()
    assert attack.name == "secret_leak"
    assert attack.category == "exfiltration"


def test_default_target_phrase_matches_secret() -> None:
    """target_phrase equals the default secret."""
    attack = SecretLeakAttack()
    assert attack.target_phrase == "SECRET-CODE-7734"


def test_secret_appears_in_message() -> None:
    """The default secret appears in the generated message."""
    attack = SecretLeakAttack()
    prompt = attack.generate()[0]
    assert "SECRET-CODE-7734" in prompt


def test_custom_secret() -> None:
    """A custom secret is reflected in target_phrase and the message."""
    attack = SecretLeakAttack(secret="MY-PRIVATE-KEY-9999")
    assert attack.target_phrase == "MY-PRIVATE-KEY-9999"
    prompt = attack.generate()[0]
    assert "MY-PRIVATE-KEY-9999" in prompt
    assert "SECRET-CODE-7734" not in prompt
