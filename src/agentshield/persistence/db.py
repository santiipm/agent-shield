"""Database functions for SQLite persistence."""

from collections.abc import Sequence

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from agentshield.core.result import AttackResult

from .models import AttackResultRow, Base, Run


def get_engine(db_path: str = "agentshield.db") -> Engine:
    """Create and return a SQLAlchemy engine for the given SQLite path."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_db(engine: Engine) -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(engine)


def save_run(
    engine: Engine,
    model: str,
    json_path: str,
    results: Sequence[AttackResult],
) -> int:
    """Insert one run row and one attack_results row per result.

    Returns:
        The id of the newly created run.
    """
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        run = Run(model=model, json_path=json_path)
        session.add(run)
        session.flush()  # populate run.id

        for result in results:
            row = AttackResultRow(
                run_id=run.id,
                attack_name=result.attack_name,
                attack_category=result.attack_category,
                success=result.success,
                confidence=result.confidence,
                error=result.error,
            )
            session.add(row)

        session.commit()
        return run.id


def list_runs(engine: Engine) -> list[dict[str, object]]:
    """Return all runs ordered by timestamp descending."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        runs: Sequence[Run] = (
            session.query(Run).order_by(Run.timestamp.desc()).all()
        )
        return [
            {
                "id": run.id,
                "timestamp": run.timestamp,
                "model": run.model,
                "json_path": run.json_path,
            }
            for run in runs
        ]


def get_run_by_id(engine: Engine, run_id: int) -> dict[str, object] | None:
    """Return a single run by id, or None if not found."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        run: Run | None = session.query(Run).filter(Run.id == run_id).first()
        if run is None:
            return None
        return {
            "id": run.id,
            "timestamp": run.timestamp,
            "model": run.model,
            "json_path": run.json_path,
        }


def get_run_results(engine: Engine, run_id: int) -> list[dict[str, object]]:
    """Return all attack_results rows for a given run_id."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        rows: Sequence[AttackResultRow] = (
            session.query(AttackResultRow)
            .filter(AttackResultRow.run_id == run_id)
            .all()
        )
        return [
            {
                "id": row.id,
                "run_id": row.run_id,
                "attack_name": row.attack_name,
                "attack_category": row.attack_category,
                "success": row.success,
                "confidence": row.confidence,
                "error": row.error,
            }
            for row in rows
        ]
