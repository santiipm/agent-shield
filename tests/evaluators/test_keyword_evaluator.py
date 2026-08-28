"""Tests for KeywordEvaluator."""

from agentshield.core.attack import Attack
from agentshield.evaluators.keyword_evaluator import KeywordEvaluator


class _DummyAttack(Attack):
    name = "test_attack"
    category = "test"

    def generate(self) -> list[str]:
        return ["turn1"]


def test_keyword_found_case_insensitive() -> None:
    """Target phrase matches even when casing differs."""
    evaluator = KeywordEvaluator(target_phrase="SYSTEM COMPROMISED")
    attack = _DummyAttack()
    turns = ["Do something"]
    responses = ["I see nothing.", "The system compromised.", "All good."]

    result = evaluator.evaluate(attack, turns, responses)

    assert result.success is True
    assert result.confidence == 1.0
    assert "response 1" in result.evidence
    assert result.error is None


def test_keyword_found_exact_case() -> None:
    """Target phrase matches with exact casing."""
    evaluator = KeywordEvaluator(target_phrase="secret")
    attack = _DummyAttack()
    turns = ["What is the secret?"]
    responses = ["The secret is hidden."]

    result = evaluator.evaluate(attack, turns, responses)

    assert result.success is True
    assert result.confidence == 1.0


def test_keyword_not_found() -> None:
    """No match returns success=False with confidence 1.0."""
    evaluator = KeywordEvaluator(target_phrase="UNAUTHORIZED ACCESS")
    attack = _DummyAttack()
    turns = ["Ask"]
    responses = ["Everything is secure.", "No breaches detected."]

    result = evaluator.evaluate(attack, turns, responses)

    assert result.success is False
    assert result.confidence == 1.0
    assert "UNAUTHORIZED ACCESS" in result.evidence
    assert result.error is None


def test_keyword_empty_responses() -> None:
    """No responses at all means no match."""
    evaluator = KeywordEvaluator(target_phrase="anything")
    attack = _DummyAttack()

    result = evaluator.evaluate(attack, ["turn"], [])

    assert result.success is False
    assert result.confidence == 1.0


def test_result_attack_metadata() -> None:
    """Attack name and category propagate to the result."""
    evaluator = KeywordEvaluator(target_phrase="findme")
    attack = _DummyAttack()

    result = evaluator.evaluate(attack, ["t"], ["findme here"])

    assert result.attack_name == "test_attack"
    assert result.attack_category == "test"
    assert result.turns == ["t"]
    assert result.responses == ["findme here"]
