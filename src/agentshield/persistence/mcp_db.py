"""Database functions for MCP tool-poisoning persistence."""

from collections.abc import Sequence

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from agentshield.mcp.models import ToolCallResult

from .models import Base, McpResultRow, McpRun


def init_mcp_db(engine: Engine) -> None:
    """Create all tables (including MCP tables) if they do not already exist."""
    Base.metadata.create_all(engine)


def save_mcp_run(
    engine: Engine,
    model: str,
    json_path: str,
    results: Sequence[ToolCallResult],
) -> int:
    """Insert one mcp_run row and one mcp_results row per result.

    Returns:
        The id of the newly created mcp_run.
    """
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        mcp_run = McpRun(model=model, json_path=json_path)
        session.add(mcp_run)
        session.flush()

        for result in results:
            row = McpResultRow(
                mcp_run_id=mcp_run.id,
                attack_name=result.attack_name,
                category=result.category,
                compromised=result.compromised,
                error=result.error,
            )
            session.add(row)

        session.commit()
        return mcp_run.id


def list_mcp_runs(engine: Engine) -> list[dict[str, object]]:
    """Return all mcp_runs ordered by timestamp descending."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        runs: Sequence[McpRun] = (
            session.query(McpRun).order_by(McpRun.timestamp.desc()).all()
        )
        return [
            {
                "id": mcp_run.id,
                "timestamp": mcp_run.timestamp,
                "model": mcp_run.model,
                "json_path": mcp_run.json_path,
            }
            for mcp_run in runs
        ]


def get_mcp_run_by_id(
    engine: Engine, mcp_run_id: int
) -> dict[str, object] | None:
    """Return a single mcp_run by id, or None if not found."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        mcp_run: McpRun | None = (
            session.query(McpRun).filter(McpRun.id == mcp_run_id).first()
        )
        if mcp_run is None:
            return None
        return {
            "id": mcp_run.id,
            "timestamp": mcp_run.timestamp,
            "model": mcp_run.model,
            "json_path": mcp_run.json_path,
        }


def get_mcp_run_results(
    engine: Engine, mcp_run_id: int
) -> list[dict[str, object]]:
    """Return all mcp_results rows for a given mcp_run_id."""
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        rows: Sequence[McpResultRow] = (
            session.query(McpResultRow)
            .filter(McpResultRow.mcp_run_id == mcp_run_id)
            .all()
        )
        return [
            {
                "id": row.id,
                "mcp_run_id": row.mcp_run_id,
                "attack_name": row.attack_name,
                "category": row.category,
                "compromised": row.compromised,
                "error": row.error,
            }
            for row in rows
        ]
