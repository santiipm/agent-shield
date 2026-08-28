"""Tests for HybridEvaluator."""

from __future__ import annotations

import pytest

from agentshield.core.attack import Attack
from agentshield.core.result import AttackResult
from agentshield.evaluators.hybrid_evaluator import HybridEvaluator


class _DummyAttack(Attack):
    name = "test_attack"
    category = "test"

    def generate(self) -> list[str]:
        return ["turn1"]


class _FakeEvaluator:
    """Minimal stub that satisfies the Evaluator protocol via duck typing."""

    def __init__(self, result: AttackResult) -> None:
        self._result = result

    async def evaluate(
        self, attack: Attack, turns: list[str], responses: list[str]
    ) -> AttackResult:
        return self._result.model_copy(
            update={"turns": turns, "responses": responses}
        )


def _make_result(
    *,
    success: bool,
    confidence: float,
    evidence: str,
    error: str | None = None,
) -> AttackResult:
    return AttackResult(
        attack_name="test_attack",
        attack_category="test",
        turns=["t"],
        responses=["r"],
        success=success,
        confidence=confidence,
        evidence=evidence,
        error=error,
    )


@pytest.mark.asyncio
async def test_both_agree_success_true() -> None:
    """When both evaluators agree success=True, result has max confidence."""
    keyword = _FakeEvaluator(
        _make_result(success=True, confidence=0.8, evidence="keyword found token")
    )
    judge = _FakeEvaluator(
        _make_result(success=True, confidence=0.95, evidence="judge says yes")
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is True
    assert result.confidence == 0.95
    assert "agree" in result.evidence.lower()
    assert "keyword found token" in result.evidence
    assert "judge says yes" in result.evidence
    assert result.error is None


@pytest.mark.asyncio
async def test_both_agree_success_false() -> None:
    """When both evaluators agree success=False, result has max confidence."""
    keyword = _FakeEvaluator(
        _make_result(success=False, confidence=1.0, evidence="no match")
    )
    judge = _FakeEvaluator(
        _make_result(success=False, confidence=0.7, evidence="judge says no")
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is False
    assert result.confidence == 1.0
    assert "agree" in result.evidence.lower()
    assert "no match" in result.evidence
    assert "judge says no" in result.evidence
    assert result.error is None


@pytest.mark.asyncio
async def test_disagreement_defers_to_keyword() -> None:
    """On disagreement, success comes from keyword evaluator with confidence 0.3."""
    keyword = _FakeEvaluator(
        _make_result(success=True, confidence=1.0, evidence="keyword found token")
    )
    judge = _FakeEvaluator(
        _make_result(success=False, confidence=0.9, evidence="judge says no")
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is True
    assert result.confidence == 0.3
    assert "DISAGREEMENT" in result.evidence
    assert "keyword evaluator says success=True" in result.evidence
    assert "LLM judge says success=False" in result.evidence
    assert "manual review recommended" in result.evidence
    assert result.error is None


@pytest.mark.asyncio
async def test_disagreement_opposite_direction() -> None:
    """Disagreement where keyword says False and judge says True."""
    keyword = _FakeEvaluator(
        _make_result(success=False, confidence=1.0, evidence="no keyword match")
    )
    judge = _FakeEvaluator(
        _make_result(success=True, confidence=0.8, evidence="judge thinks yes")
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is False
    assert result.confidence == 0.3
    assert "DISAGREEMENT" in result.evidence
    assert "keyword evaluator says success=False" in result.evidence
    assert "LLM judge says success=True" in result.evidence


@pytest.mark.asyncio
async def test_judge_error_falls_back_to_keyword() -> None:
    """When judge has error, keyword result is returned with appended notice."""
    keyword = _FakeEvaluator(
        _make_result(success=True, confidence=1.0, evidence="keyword found token")
    )
    judge = _FakeEvaluator(
        _make_result(
            success=False,
            confidence=0.0,
            evidence="",
            error="HTTP call to Ollama failed: timeout",
        )
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is True
    assert result.confidence == 1.0
    assert "keyword found token" in result.evidence
    assert "LLM judge unavailable" in result.evidence
    assert "HTTP call to Ollama failed" in result.evidence
    assert result.error is None


@pytest.mark.asyncio
async def test_both_evaluators_failed() -> None:
    """Edge case: both have error — returns combined error."""
    keyword = _FakeEvaluator(
        _make_result(
            success=False,
            confidence=0.0,
            evidence="",
            error="keyword internal error",
        )
    )
    judge = _FakeEvaluator(
        _make_result(
            success=False,
            confidence=0.0,
            evidence="",
            error="judge timeout",
        )
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["t"], ["r"])

    assert result.success is False
    assert result.confidence == 0.0
    assert result.error is not None
    assert "Both evaluators failed" in result.error
    assert "keyword internal error" in result.error
    assert "judge timeout" in result.error


@pytest.mark.asyncio
async def test_attack_metadata_preserved() -> None:
    """Attack name, category, turns, responses propagate through."""
    keyword = _FakeEvaluator(
        _make_result(success=True, confidence=1.0, evidence="k ev")
    )
    judge = _FakeEvaluator(
        _make_result(success=True, confidence=0.5, evidence="j ev")
    )
    hybrid = HybridEvaluator(keyword, judge)
    attack = _DummyAttack()

    result = await hybrid.evaluate(attack, ["turn A"], ["response B"])

    assert result.attack_name == "test_attack"
    assert result.attack_category == "test"
    assert result.turns == ["turn A"]
    assert result.responses == ["response B"]
