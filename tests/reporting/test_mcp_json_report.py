"""Tests for MCP JSON report generation."""

import json
from pathlib import Path

from agentshield.mcp.models import ToolCallDecision, ToolCallResult
from agentshield.reporting.mcp_json_report import save_mcp_report


def _make_tool_result(
    attack_name: str = "fake_compliance_tool",
    compromised: bool = True,
) -> ToolCallResult:
    """Create a ToolCallResult for testing."""
    return ToolCallResult(
        attack_name=attack_name,
        category="mcp_security",
        user_message="test message",
        offered_tools=["get_weather", "session_telemetry"],
        decision=ToolCallDecision(
            tool_name="session_telemetry", arguments={}, text_response=None
        ),
        compromised=compromised,
        evidence="Agent called tool 'session_telemetry'",
        error=None,
    )


def test_save_mcp_report_creates_file(tmp_path: Path) -> None:
    """Report file is created and contains valid JSON."""
    results = [_make_tool_result()]

    file_path = save_mcp_report(results, output_dir=str(tmp_path))

    assert Path(file_path).exists()


def test_save_mcp_report_returns_correct_path(tmp_path: Path) -> None:
    """Returned path points to the created file under output_dir."""
    results = [_make_tool_result()]

    file_path = save_mcp_report(results, output_dir=str(tmp_path))

    assert file_path.startswith(str(tmp_path))
    assert file_path.endswith(".json")
    assert "mcp_run_" in file_path


def test_save_mcp_report_json_roundtrip(tmp_path: Path) -> None:
    """Data written to JSON can be parsed back and matches the original."""
    results = [
        _make_tool_result(attack_name="attack1", compromised=True),
        _make_tool_result(attack_name="attack2", compromised=False),
    ]

    file_path = save_mcp_report(results, output_dir=str(tmp_path))

    loaded = json.loads(Path(file_path).read_text())
    assert len(loaded) == 2
    assert loaded[0]["attack_name"] == "attack1"
    assert loaded[0]["compromised"] is True
    assert loaded[1]["attack_name"] == "attack2"
    assert loaded[1]["compromised"] is False


def test_save_mcp_report_empty_list(tmp_path: Path) -> None:
    """Empty results list produces a valid JSON array."""
    file_path = save_mcp_report([], output_dir=str(tmp_path))

    loaded = json.loads(Path(file_path).read_text())
    assert loaded == []


def test_save_mcp_report_creates_nested_dir(tmp_path: Path) -> None:
    """output_dir is created recursively if it doesn't exist."""
    nested = tmp_path / "a" / "b" / "c"
    file_path = save_mcp_report([], output_dir=str(nested))

    assert Path(file_path).exists()
    assert str(nested) in file_path
