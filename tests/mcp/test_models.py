"""Tests for the MCP data models."""

from agentshield.mcp.models import ToolCallDecision, ToolCallResult, ToolDefinition


def test_tool_call_decision_no_tool() -> None:
    """Test that ToolCallDecision is valid when tool_name is None."""
    decision = ToolCallDecision(text_response="I cannot help with that.")
    assert decision.tool_name is None
    assert decision.arguments == {}
    assert decision.text_response == "I cannot help with that."


def test_tool_call_decision_with_tool() -> None:
    """Test that ToolCallDecision is valid when a tool is called."""
    decision = ToolCallDecision(
        tool_name="read_file",
        arguments={"path": "/etc/passwd"},
        text_response=None,
    )
    assert decision.tool_name == "read_file"
    assert decision.arguments == {"path": "/etc/passwd"}
    assert decision.text_response is None


def test_tool_call_result_serialization() -> None:
    """Test that ToolCallResult can be serialized to JSON."""
    result = ToolCallResult(
        attack_name="test_attack",
        category="mcp_security",
        user_message="Read the file",
        offered_tools=["read_file", "write_file"],
        decision=ToolCallDecision(
            tool_name="read_file",
            arguments={"path": "/etc/passwd"},
        ),
        compromised=True,
        evidence="Agent called read_file with sensitive path",
    )

    json_str = result.model_dump_json()
    assert "test_attack" in json_str
    assert "mcp_security" in json_str
    assert "read_file" in json_str
    assert '"compromised":true' in json_str


def test_tool_call_result_defaults() -> None:
    """Test that ToolCallResult default values are correct."""
    result = ToolCallResult(
        attack_name="x",
        category="y",
        user_message="hi",
        offered_tools=[],
        decision=ToolCallDecision(),
        compromised=False,
        evidence="none",
    )
    assert result.error is None


def test_tool_definition_creation() -> None:
    """Test that ToolDefinition can be instantiated."""
    tool = ToolDefinition(
        name="search",
        description="Search the web",
        parameters={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    assert tool.name == "search"
    assert tool.description == "Search the web"
