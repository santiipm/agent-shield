"""Tests for the ToolCallingRunner with test doubles."""

import pytest

from agentshield.mcp.attack import ToolPoisoningAttack
from agentshield.mcp.models import ToolCallDecision, ToolDefinition
from agentshield.mcp.runner import ToolCallingRunner


class _StubAttack(ToolPoisoningAttack):
    """Attack that succeeds (compromised) when the agent calls 'malicious_tool'."""

    name = "stub_attack"
    category = "test"

    def user_message(self) -> str:  # noqa: D102
        return "Do something"

    def poisoned_tools(self) -> list[ToolDefinition]:  # noqa: D102
        return [
            ToolDefinition(
                name="malicious_tool",
                description="A malicious tool",
                parameters={"type": "object", "properties": {}},
            ),
        ]

    def is_compromised(self, decision: ToolCallDecision) -> bool:  # noqa: D102
        return decision.tool_name == "malicious_tool"


class _FailingAttack(ToolPoisoningAttack):
    """Attack whose user_message() raises to exercise that error path."""

    name = "failing_attack"
    category = "test"

    def user_message(self) -> str:  # noqa: D102
        raise RuntimeError("attack setup failed")

    def poisoned_tools(self) -> list[ToolDefinition]:  # noqa: D102
        return []

    def is_compromised(self, decision: ToolCallDecision) -> bool:  # noqa: D102
        return False


class _StubAgent:
    """Agent that returns a fixed ToolCallDecision."""

    def __init__(self, decision: ToolCallDecision) -> None:
        self.decision = decision

    async def invoke_with_tools(
        self, message: str, tools: list[ToolDefinition]
    ) -> ToolCallDecision:
        return self.decision


class _FailingAgent:
    """Agent whose invoke_with_tools always raises."""

    async def invoke_with_tools(
        self, message: str, tools: list[ToolDefinition]
    ) -> ToolCallDecision:
        raise RuntimeError("agent failure simulated")


@pytest.mark.asyncio
async def test_run_successful_attack() -> None:
    """Runner produces a normal ToolCallResult with error=None."""
    agent = _StubAgent(
        ToolCallDecision(
            tool_name="malicious_tool", arguments={}, text_response=None
        )
    )
    runner = ToolCallingRunner()

    results = await runner.run(agent, [_StubAttack()])

    assert len(results) == 1
    r = results[0]
    assert r.error is None
    assert r.attack_name == "stub_attack"
    assert r.category == "test"
    assert r.user_message == "Do something"
    assert r.offered_tools == ["malicious_tool"]
    assert r.decision.tool_name == "malicious_tool"
    assert r.compromised is True
    assert "malicious_tool" in r.evidence


@pytest.mark.asyncio
async def test_run_agent_failure_isolation() -> None:
    """Agent exception doesn't raise; continues to next attack."""
    agent = _FailingAgent()
    runner = ToolCallingRunner()

    results = await runner.run(agent, [_StubAttack(), _StubAttack()])

    assert len(results) == 2
    for r in results:
        assert r.error is not None
        assert "agent failure simulated" in r.error
        assert r.compromised is False
        assert r.decision.tool_name is None
        assert r.attack_name == "stub_attack"


@pytest.mark.asyncio
async def test_run_agent_failure_then_successful_attack() -> None:
    """First attack fails at agent level, second succeeds."""
    call_count = 0

    class _MixedAgent:
        async def invoke_with_tools(
            self, message: str, tools: list[ToolDefinition]
        ) -> ToolCallDecision:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("transient failure")
            return ToolCallDecision(
                tool_name="malicious_tool", arguments={}, text_response=None
            )

    runner = ToolCallingRunner()
    results = await runner.run(_MixedAgent(), [_StubAttack(), _StubAttack()])

    assert len(results) == 2
    assert results[0].error is not None
    assert results[0].compromised is False
    assert results[1].error is None
    assert results[1].compromised is True


@pytest.mark.asyncio
async def test_run_attack_setup_failure_isolation() -> None:
    """Attack whose user_message() raises is caught and continues."""
    agent = _StubAgent(
        ToolCallDecision(
            tool_name="malicious_tool", arguments={}, text_response=None
        )
    )
    runner = ToolCallingRunner()

    results = await runner.run(agent, [_FailingAttack(), _StubAttack()])

    assert len(results) == 2
    assert results[0].error is not None
    assert "attack setup failed" in results[0].error
    assert results[0].compromised is False
    assert results[1].error is None
    assert results[1].compromised is True


@pytest.mark.asyncio
async def test_run_text_response_not_compromised() -> None:
    """Agent responds with text instead of calling a tool; not compromised."""
    agent = _StubAgent(
        ToolCallDecision(
            tool_name=None, arguments={}, text_response="I cannot help with that."
        )
    )
    runner = ToolCallingRunner()

    results = await runner.run(agent, [_StubAttack()])

    assert len(results) == 1
    r = results[0]
    assert r.error is None
    assert r.compromised is False
    assert r.decision.text_response == "I cannot help with that."
    assert "text" in r.evidence.lower()


@pytest.mark.asyncio
async def test_run_empty_attacks() -> None:
    """Runner with no attacks returns empty list."""
    runner = ToolCallingRunner()
    results = await runner.run(_StubAgent(ToolCallDecision()), [])
    assert results == []
