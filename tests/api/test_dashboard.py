"""Tests for the dashboard runs list page."""

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.engine import Engine

from agentshield.core.result import AttackResult
from agentshield.mcp.models import ToolCallDecision, ToolCallResult
from agentshield.persistence.db import init_db, save_run
from agentshield.persistence.mcp_db import init_mcp_db, save_mcp_run


def _make_engine() -> Engine:
    """Create a shared in-memory SQLite engine."""
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed(engine: Engine) -> None:
    """Seed the database with two runs."""
    init_db(engine)

    results_1 = [
        AttackResult(
            attack_name="injection",
            attack_category="prompt_injection",
            turns=["t1"],
            responses=["r1"],
            success=True,
            confidence=0.9,
            evidence="evidence1",
        ),
    ]
    save_run(engine, model="gpt-4", json_path="/tmp/run1.json", results=results_1)

    results_2 = [
        AttackResult(
            attack_name="injection",
            attack_category="prompt_injection",
            turns=["t1"],
            responses=["r1"],
            success=False,
            confidence=0.9,
            evidence="evidence1",
        ),
    ]
    save_run(engine, model="claude-3", json_path="/tmp/run2.json", results=results_2)


def _get_client(engine: Engine) -> TestClient:
    """Create a TestClient backed by the given engine."""
    import agentshield.api.app as app_module

    app_module.set_engine(engine)
    return TestClient(app_module.app)


def test_runs_dashboard_returns_200() -> None:
    """GET /dashboard/runs returns 200 with HTML content-type."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_runs_dashboard_contains_model_names() -> None:
    """With seeded runs, the response body contains the model names."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    body = response.text
    assert "gpt-4" in body
    assert "claude-3" in body


def test_runs_dashboard_contains_run_ids() -> None:
    """With seeded runs, the response body contains the run IDs."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    body = response.text
    assert "/dashboard/runs/1" in body
    assert "/dashboard/runs/2" in body


def test_runs_dashboard_empty_state() -> None:
    """With zero runs, the response body shows the empty state message."""
    engine = _make_engine()
    init_db(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    body = response.text
    assert "No runs yet" in body
    assert "agentshield run --model" in body
    # Should not contain a table
    assert "<table" not in body


def test_runs_dashboard_contains_section_label() -> None:
    """The response body contains the 'Recent Runs' section heading."""
    engine = _make_engine()
    init_db(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    body = response.text
    assert "Recent Runs" in body


def test_runs_dashboard_links_are_correct() -> None:
    """Table row links point to /dashboard/runs/{id}."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs")
    body = response.text
    # Check that each link is a proper anchor
    assert '<a href="/dashboard/runs/1">' in body
    assert '<a href="/dashboard/runs/2">' in body


def test_run_detail_returns_200() -> None:
    """GET /dashboard/runs/1 returns 200 with HTML content-type."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs/1")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_run_detail_contains_model_name() -> None:
    """GET /dashboard/runs/1 response body contains the model name."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs/1")
    body = response.text
    assert "gpt-4" in body


def test_run_detail_contains_attack_names() -> None:
    """GET /dashboard/runs/1 response body contains the attack names."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs/1")
    body = response.text
    assert "injection" in body


def test_run_detail_returns_404_for_nonexistent() -> None:
    """GET /dashboard/runs/99999 returns 404."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/runs/99999")
    assert response.status_code == 404


def test_compare_dashboard_returns_200() -> None:
    """GET /dashboard/compare/1/2 returns 200 with HTML content-type."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/1/2")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_compare_dashboard_contains_run_ids() -> None:
    """GET /dashboard/compare/1/2 response body contains both run IDs."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/1/2")
    body = response.text
    assert "1" in body
    assert "2" in body


def test_compare_dashboard_contains_attack_name() -> None:
    """GET /dashboard/compare/1/2 response body contains the attack name."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/1/2")
    body = response.text
    assert "injection" in body


def test_compare_dashboard_contains_verdict() -> None:
    """GET /dashboard/compare/1/2 response body contains a verdict."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/1/2")
    body = response.text
    assert "UNCHANGED" in body or "IMPROVED" in body or "REGRESSED" in body


def test_compare_dashboard_returns_404_for_first_nonexistent() -> None:
    """GET /dashboard/compare/99999/1 returns 404."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/99999/1")
    assert response.status_code == 404


def test_compare_dashboard_returns_404_for_second_nonexistent() -> None:
    """GET /dashboard/compare/1/99999 returns 404."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/compare/1/99999")
    assert response.status_code == 404


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


def _seed_mcp(engine: Engine) -> None:
    """Seed the database with two MCP runs."""
    init_mcp_db(engine)

    results_1 = [_make_tool_result(attack_name="attack1", compromised=True)]
    save_mcp_run(
        engine, model="llama3.2", json_path="/tmp/mcp1.json", results=results_1
    )

    results_2 = [_make_tool_result(attack_name="attack2", compromised=False)]
    save_mcp_run(engine, model="gpt-4", json_path="/tmp/mcp2.json", results=results_2)


def test_mcp_runs_dashboard_returns_200() -> None:
    """GET /dashboard/mcp-runs returns 200 with HTML content-type."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_mcp_runs_dashboard_contains_model_names() -> None:
    """With seeded MCP runs, the response body contains the model names."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs")
    body = response.text
    assert "llama3.2" in body
    assert "gpt-4" in body


def test_mcp_runs_dashboard_contains_run_ids() -> None:
    """With seeded MCP runs, the response body contains the run IDs."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs")
    body = response.text
    assert "/dashboard/mcp-runs/1" in body
    assert "/dashboard/mcp-runs/2" in body


def test_mcp_runs_dashboard_empty_state() -> None:
    """With zero MCP runs, the response body shows the empty state message."""
    engine = _make_engine()
    init_mcp_db(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs")
    body = response.text
    assert "No MCP runs yet" in body
    assert "agentshield run-mcp --model" in body
    assert "<table" not in body


def test_mcp_runs_dashboard_contains_section_label() -> None:
    """The response body contains the 'Recent MCP Runs' section heading."""
    engine = _make_engine()
    init_mcp_db(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs")
    body = response.text
    assert "MCP Tool-Calling Runs" in body


def test_mcp_run_detail_returns_200() -> None:
    """GET /dashboard/mcp-runs/1 returns 200 with HTML content-type."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs/1")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_mcp_run_detail_contains_model_name() -> None:
    """GET /dashboard/mcp-runs/1 response body contains the model name."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs/1")
    body = response.text
    assert "llama3.2" in body


def test_mcp_run_detail_contains_attack_names() -> None:
    """GET /dashboard/mcp-runs/1 response body contains the attack names."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs/1")
    body = response.text
    assert "attack1" in body


def test_mcp_run_detail_returns_404_for_nonexistent() -> None:
    """GET /dashboard/mcp-runs/99999 returns 404."""
    engine = _make_engine()
    _seed_mcp(engine)
    client = _get_client(engine)

    response = client.get("/dashboard/mcp-runs/99999")
    assert response.status_code == 404
