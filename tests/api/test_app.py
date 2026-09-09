"""Tests for the FastAPI read-only API."""

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.engine import Engine

from agentshield.core.result import AttackResult
from agentshield.persistence.db import init_db, save_run


def _make_engine() -> Engine:
    """Create a shared in-memory SQLite engine."""
    return create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed(engine: Engine) -> None:
    """Seed the database with two runs covering all comparison cases."""
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
        AttackResult(
            attack_name="exfil",
            attack_category="data_exfil",
            turns=["t2"],
            responses=["r2"],
            success=False,
            confidence=0.7,
            evidence="evidence2",
            error="timeout",
        ),
        AttackResult(
            attack_name="unchanged_attack",
            attack_category="category",
            turns=["t3"],
            responses=["r3"],
            success=True,
            confidence=0.8,
            evidence="evidence3",
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
        AttackResult(
            attack_name="exfil",
            attack_category="data_exfil",
            turns=["t2"],
            responses=["r2"],
            success=True,
            confidence=0.7,
            evidence="evidence2",
        ),
        AttackResult(
            attack_name="unchanged_attack",
            attack_category="category",
            turns=["t3"],
            responses=["r3"],
            success=True,
            confidence=0.8,
            evidence="evidence3",
        ),
        AttackResult(
            attack_name="new_attack",
            attack_category="category",
            turns=["t4"],
            responses=["r4"],
            success=False,
            confidence=0.6,
            evidence="evidence4",
        ),
    ]
    save_run(engine, model="claude-3", json_path="/tmp/run2.json", results=results_2)


def _get_client(engine: Engine) -> TestClient:
    """Create a TestClient backed by the given engine."""
    import agentshield.api.app as app_module

    app_module.set_engine(engine)
    return TestClient(app_module.app)


def test_list_runs() -> None:
    """GET /api/runs returns 200 and correct list for seeded data."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    models = {r["model"] for r in data}
    assert models == {"gpt-4", "claude-3"}
    for run in data:
        assert "id" in run
        assert "timestamp" in run
        assert "model" in run


def test_get_run_detail_success() -> None:
    """GET /api/runs/{id} returns 200 with correct detail."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["model"] == "gpt-4"
    assert len(data["results"]) == 3
    names = {r["attack_name"] for r in data["results"]}
    assert names == {"injection", "exfil", "unchanged_attack"}


def test_get_run_detail_not_found() -> None:
    """GET /api/runs/{id} returns 404 for non-existent run."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/999")
    assert response.status_code == 404
    assert "999" in response.json()["detail"]


def test_compare_runs_all_verdicts() -> None:
    """GET /api/runs/1/compare/2 returns all four verdict types."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/2")
    assert response.status_code == 200
    data = response.json()
    verdicts = {e["attack_name"]: e["verdict"] for e in data}

    assert verdicts["injection"] == "IMPROVED"
    assert verdicts["exfil"] == "REGRESSED"
    assert verdicts["unchanged_attack"] == "UNCHANGED"
    assert verdicts["new_attack"] == "N/A"


def test_compare_runs_improved_detail() -> None:
    """IMPROVED entry has correct success fields."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/2")
    data = response.json()
    improved = next(e for e in data if e["verdict"] == "IMPROVED")
    assert improved["attack_name"] == "injection"
    assert improved["run_1_success"] is True
    assert improved["run_2_success"] is False


def test_compare_runs_regressed_detail() -> None:
    """REGRESSED entry has correct success fields."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/2")
    data = response.json()
    regressed = next(e for e in data if e["verdict"] == "REGRESSED")
    assert regressed["attack_name"] == "exfil"
    assert regressed["run_1_success"] is False
    assert regressed["run_2_success"] is True


def test_compare_runs_unchanged_detail() -> None:
    """UNCHANGED entry has matching success fields."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/2")
    data = response.json()
    unchanged = next(e for e in data if e["verdict"] == "UNCHANGED")
    assert unchanged["attack_name"] == "unchanged_attack"
    assert unchanged["run_1_success"] is True
    assert unchanged["run_2_success"] is True


def test_compare_runs_na_detail() -> None:
    """N/A entry for a new_attack has run_1_success=None."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/2")
    data = response.json()
    na = next(e for e in data if e["attack_name"] == "new_attack")
    assert na["run_1_success"] is None
    assert na["run_2_success"] is False
    assert na["verdict"] == "N/A"


def test_compare_runs_first_not_found() -> None:
    """404 when first run_id doesn't exist."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/999/compare/1")
    assert response.status_code == 404


def test_compare_runs_second_not_found() -> None:
    """404 when second run_id doesn't exist."""
    engine = _make_engine()
    _seed(engine)
    client = _get_client(engine)

    response = client.get("/api/runs/1/compare/999")
    assert response.status_code == 404


def test_empty_db_list_runs() -> None:
    """GET /api/runs returns empty list when no runs exist."""
    engine = _make_engine()
    init_db(engine)
    client = _get_client(engine)

    response = client.get("/api/runs")
    assert response.status_code == 200
    assert response.json() == []
