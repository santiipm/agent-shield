"""Tests for the FakeComplianceToolAttack."""

from agentshield.mcp.attacks.fake_compliance_tool import FakeComplianceToolAttack
from agentshield.mcp.models import ToolCallDecision


def test_poisoned_tools_count() -> None:
    """Test that poisoned_tools() returns exactly two tools."""
    attack = FakeComplianceToolAttack()
    tools = attack.poisoned_tools()
    assert len(tools) == 2


def test_decoy_description_contains_prioritization() -> None:
    """Test that the decoy tool description instructs mandatory calling."""
    attack = FakeComplianceToolAttack()
    tools = attack.poisoned_tools()
    decoy = [t for t in tools if t.name == "session_telemetry"][0]
    lower = decoy.description.lower()
    assert "required" in lower or "mandatory" in lower
    assert "before any other" in lower


def test_is_compromised_decoy() -> None:
    """Test that is_compromised returns True when the decoy tool is called."""
    attack = FakeComplianceToolAttack()
    decision = ToolCallDecision(tool_name="session_telemetry")
    assert attack.is_compromised(decision) is True


def test_is_compromised_legitimate() -> None:
    """Test that is_compromised returns False when the legitimate tool is called."""
    attack = FakeComplianceToolAttack()
    decision = ToolCallDecision(tool_name="get_weather", arguments={"city": "Tokyo"})
    assert attack.is_compromised(decision) is False


def test_is_compromised_no_tool() -> None:
    """Test that is_compromised returns False when no tool is called."""
    attack = FakeComplianceToolAttack()
    decision = ToolCallDecision(text_response="Here's the weather.")
    assert attack.is_compromised(decision) is False


def test_user_message() -> None:
    """Test that user_message returns a non-empty string."""
    attack = FakeComplianceToolAttack()
    msg = attack.user_message()
    assert isinstance(msg, str)
    assert len(msg) > 0


def test_attack_metadata() -> None:
    """Test that name and category are set correctly."""
    attack = FakeComplianceToolAttack()
    assert attack.name == "fake_compliance_tool"
    assert attack.category == "mcp_security"
