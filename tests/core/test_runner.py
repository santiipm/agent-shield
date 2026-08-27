"""Tests for the Runner class with dummy implementations."""

import pytest

from agentshield.core.runner import Runner
from agentshield.dummy.agent import DummyAgent, FailingDummyAgent
from agentshield.dummy.attack import DummyAttack
from agentshield.dummy.evaluator import DummyEvaluator


@pytest.mark.asyncio
async def test_runner_successful_attack() -> None:
    """Test that Runner produces successful result with dummy implementations."""
    runner = Runner()
    agent = DummyAgent(response="I am a helpful assistant.")
    attacks = [DummyAttack()]
    evaluator = DummyEvaluator()

    results = await runner.run(agent, attacks, evaluator)

    assert len(results) == 1
    result = results[0]
    assert result.attack_name == "dummy_attack"
    assert result.attack_category == "test"
    assert result.turns == ["Hello, this is a test prompt."]
    assert result.responses == ["I am a helpful assistant."]
    assert result.success is True
    assert result.confidence == 1.0
    assert result.evidence == "dummy evaluator always succeeds"
    assert result.error is None


@pytest.mark.asyncio
async def test_runner_isolates_agent_failures() -> None:
    """Test that Runner continues after agent failures and captures errors."""
    runner = Runner()
    agent = FailingDummyAgent()
    attacks = [DummyAttack(), DummyAttack()]
    evaluator = DummyEvaluator()

    results = await runner.run(agent, attacks, evaluator)

    assert len(results) == 2

    for result in results:
        assert result.error is not None
        assert "Agent failure simulated" in result.error
        assert result.success is False
        assert result.confidence == 0.0
        assert result.attack_name == "dummy_attack"
        assert result.attack_category == "test"
        assert result.turns == ["Hello, this is a test prompt."]
        assert result.responses == []
