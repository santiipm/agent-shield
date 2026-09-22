"""Tests for MCP persistence layer."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from agentshield.mcp.models import ToolCallDecision, ToolCallResult
from agentshield.persistence.mcp_db import (
    get_mcp_run_by_id,
    get_mcp_run_results,
    init_mcp_db,
    list_mcp_runs,
    save_mcp_run,
)
from agentshield.persistence.models import McpResultRow, McpRun


def _make_engine() -> Engine:
    """Create an in-memory SQLite engine."""
    return create_engine("sqlite:///:memory:", echo=False)


def _make_tool_result(
    attack_name: str = "fake_compliance_tool",
    category: str = "mcp_security",
    compromised: bool = True,
    error: str | None = None,
) -> ToolCallResult:
    """Create a ToolCallResult for testing."""
    return ToolCallResult(
        attack_name=attack_name,
        category=category,
        user_message="test message",
        offered_tools=["get_weather", "session_telemetry"],
        decision=ToolCallDecision(
            tool_name="session_telemetry", arguments={}, text_response=None
        ),
        compromised=compromised,
        evidence="Agent called tool 'session_telemetry'",
        error=error,
    )


def test_init_mcp_db_creates_tables() -> None:
    """init_mcp_db creates mcp_runs and mcp_results tables."""
    engine = _make_engine()
    init_mcp_db(engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "mcp_runs" in table_names
    assert "mcp_results" in table_names


def test_save_mcp_run_creates_rows() -> None:
    """save_mcp_run creates 1 mcp_run row and 2 mcp_results rows."""
    engine = _make_engine()
    init_mcp_db(engine)

    results = [
        _make_tool_result(attack_name="attack1", compromised=True),
        _make_tool_result(attack_name="attack2", compromised=False),
    ]

    run_id = save_mcp_run(
        engine, model="llama3.2", json_path="/tmp/mcp_report.json", results=results
    )

    assert isinstance(run_id, int)
    assert run_id > 0

    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        run_count = session.query(McpRun).count()
        assert run_count == 1
        ar_count = session.query(McpResultRow).count()
        assert ar_count == 2


def test_list_mcp_runs_returns_correct_fields() -> None:
    """list_mcp_runs returns the saved run with correct fields."""
    engine = _make_engine()
    init_mcp_db(engine)

    results = [_make_tool_result()]
    save_mcp_run(
        engine, model="llama3.2", json_path="/tmp/mcp.json", results=results
    )
    runs = list_mcp_runs(engine)

    assert len(runs) == 1
    run = runs[0]
    assert run["id"] == 1
    assert run["model"] == "llama3.2"
    assert run["json_path"] == "/tmp/mcp.json"
    assert run["timestamp"] is not None


def test_get_mcp_run_results_returns_correct_rows() -> None:
    """get_mcp_run_results returns mcp_results with correct values."""
    engine = _make_engine()
    init_mcp_db(engine)

    results = [
        _make_tool_result(attack_name="attack_a", compromised=True),
        _make_tool_result(attack_name="attack_b", compromised=False, error="timeout"),
    ]

    run_id = save_mcp_run(
        engine, model="llama3.2", json_path="/tmp/mcp.json", results=results
    )
    rows = get_mcp_run_results(engine, run_id)

    assert len(rows) == 2
    assert rows[0]["attack_name"] == "attack_a"
    assert rows[0]["compromised"] is True
    assert rows[1]["attack_name"] == "attack_b"
    assert rows[1]["compromised"] is False
    assert rows[1]["error"] == "timeout"


def test_list_mcp_runs_ordering() -> None:
    """list_mcp_runs returns runs ordered by timestamp descending."""
    engine = _make_engine()
    init_mcp_db(engine)

    results = [_make_tool_result()]

    save_mcp_run(engine, model="first", json_path="/tmp/1.json", results=results)
    save_mcp_run(engine, model="second", json_path="/tmp/2.json", results=results)

    runs = list_mcp_runs(engine)
    assert len(runs) == 2
    assert runs[0]["model"] == "second"
    assert runs[1]["model"] == "first"


def test_get_mcp_run_by_id_found() -> None:
    """get_mcp_run_by_id returns the run when it exists."""
    engine = _make_engine()
    init_mcp_db(engine)

    results = [_make_tool_result()]
    save_mcp_run(
        engine, model="llama3.2", json_path="/tmp/mcp.json", results=results
    )
    mcp_run = get_mcp_run_by_id(engine, 1)

    assert mcp_run is not None
    assert mcp_run["id"] == 1
    assert mcp_run["model"] == "llama3.2"
    assert mcp_run["json_path"] == "/tmp/mcp.json"
    assert mcp_run["timestamp"] is not None


def test_get_mcp_run_by_id_not_found() -> None:
    """get_mcp_run_by_id returns None when the run does not exist."""
    engine = _make_engine()
    init_mcp_db(engine)

    mcp_run = get_mcp_run_by_id(engine, 999)
    assert mcp_run is None
