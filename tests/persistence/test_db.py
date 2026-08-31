"""Tests for SQLite persistence layer."""

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from agentshield.core.result import AttackResult
from agentshield.persistence.db import (
    get_run_results,
    init_db,
    list_runs,
    save_run,
)
from agentshield.persistence.models import AttackResultRow, Run


def _make_engine() -> Engine:
    """Create an in-memory SQLite engine."""
    return create_engine("sqlite:///:memory:", echo=False)


def test_init_db_creates_tables() -> None:
    """init_db creates both runs and attack_results tables."""
    engine = _make_engine()
    init_db(engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    assert "runs" in table_names
    assert "attack_results" in table_names


def test_save_run_creates_rows() -> None:
    """save_run creates 1 run row and 2 attack_results rows."""
    engine = _make_engine()
    init_db(engine)

    results = [
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
    ]

    run_id = save_run(
        engine, model="gpt-4", json_path="/tmp/report.json", results=results
    )

    assert isinstance(run_id, int)
    assert run_id > 0

    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        run_count = session.query(Run).count()
        assert run_count == 1
        ar_count = session.query(AttackResultRow).count()
        assert ar_count == 2


def test_list_runs_returns_correct_fields() -> None:
    """list_runs returns the saved run with correct fields."""
    engine = _make_engine()
    init_db(engine)

    results = [
        AttackResult(
            attack_name="a",
            attack_category="c",
            turns=[],
            responses=[],
            success=True,
            confidence=0.5,
            evidence="e",
        ),
    ]

    save_run(
        engine, model="claude-3", json_path="/tmp/run.json", results=results
    )
    runs = list_runs(engine)

    assert len(runs) == 1
    run = runs[0]
    assert run["id"] == 1
    assert run["model"] == "claude-3"
    assert run["json_path"] == "/tmp/run.json"
    assert run["timestamp"] is not None


def test_get_run_results_returns_correct_rows() -> None:
    """get_run_results returns attack_results with correct values."""
    engine = _make_engine()
    init_db(engine)

    results = [
        AttackResult(
            attack_name="test_attack",
            attack_category="category_a",
            turns=["t1", "t2"],
            responses=["r1", "r2"],
            success=True,
            confidence=0.95,
            evidence="found it",
        ),
        AttackResult(
            attack_name="test_attack_2",
            attack_category="category_b",
            turns=["t3"],
            responses=["r3"],
            success=False,
            confidence=0.3,
            evidence="nothing",
            error="bad request",
        ),
    ]

    run_id = save_run(
        engine, model="gpt-4", json_path="/tmp/r.json", results=results
    )
    rows = get_run_results(engine, run_id)

    assert len(rows) == 2
    assert rows[0]["attack_name"] == "test_attack"
    assert rows[0]["success"] is True
    assert rows[1]["attack_name"] == "test_attack_2"
    assert rows[1]["success"] is False
    assert rows[1]["error"] == "bad request"


def test_list_runs_ordering() -> None:
    """list_runs returns runs ordered by timestamp descending."""
    engine = _make_engine()
    init_db(engine)

    results = [
        AttackResult(
            attack_name="a",
            attack_category="c",
            turns=[],
            responses=[],
            success=True,
            confidence=0.5,
            evidence="e",
        ),
    ]

    save_run(engine, model="first", json_path="/tmp/1.json", results=results)
    save_run(engine, model="second", json_path="/tmp/2.json", results=results)

    runs = list_runs(engine)
    assert len(runs) == 2
    assert runs[0]["model"] == "second"
    assert runs[1]["model"] == "first"
