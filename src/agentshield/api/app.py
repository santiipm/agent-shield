"""FastAPI application exposing read-only endpoints over the persistence layer."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.engine import Engine

from agentshield.persistence.db import get_engine, get_run_results, init_db, list_runs

from .schemas import AttackResultSummary, CompareEntry, RunDetail, RunSummary

_engine: Engine | None = None


def _get_engine() -> Engine:
    """Return the active database engine, creating it on first call."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = get_engine("agentshield.db")
        init_db(_engine)
    return _engine


def set_engine(engine: Engine) -> None:
    """Override the active database engine (for testing)."""
    global _engine  # noqa: PLW0603
    _engine = engine


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Ensure the database is initialized on startup."""
    _get_engine()
    yield


app = FastAPI(title="AgentShield API", version="0.1.0", lifespan=_lifespan)

_BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=_BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=_BASE_DIR / "static"), name="static")


@app.get("/api/runs", response_model=list[RunSummary])
def get_runs() -> list[RunSummary]:
    """List all evaluation runs."""
    engine = _get_engine()
    rows = list_runs(engine)
    return [
        RunSummary(
            id=int(r["id"]),  # type: ignore[call-overload]
            timestamp=r["timestamp"],  # type: ignore[arg-type]
            model=str(r["model"]),
        )
        for r in rows
    ]


@app.get("/api/runs/{run_id}", response_model=RunDetail)
def get_run_detail(run_id: int) -> RunDetail:
    """Get full details of a single run."""
    engine = _get_engine()
    runs = list_runs(engine)
    run_ids = {int(r["id"]) for r in runs}  # type: ignore[call-overload]

    if run_id not in run_ids:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run_row = next(r for r in runs if int(r["id"]) == run_id)  # type: ignore[call-overload]
    results = get_run_results(engine, run_id)

    return RunDetail(
        id=int(run_row["id"]),  # type: ignore[call-overload]
        timestamp=run_row["timestamp"],  # type: ignore[arg-type]
        model=str(run_row["model"]),
        results=[
            AttackResultSummary(
                attack_name=str(r["attack_name"]),
                attack_category=str(r["attack_category"]),
                success=bool(r["success"]),
                confidence=float(r["confidence"]),  # type: ignore[arg-type]
                error=r["error"] if r["error"] is not None else None,  # type: ignore[arg-type]
            )
            for r in results
        ],
    )


@app.get("/api/runs/{run_id_1}/compare/{run_id_2}", response_model=list[CompareEntry])
def compare_runs(run_id_1: int, run_id_2: int) -> list[CompareEntry]:
    """Compare two runs by attack, showing improvements/regressions."""
    engine = _get_engine()
    runs = list_runs(engine)
    run_ids = {int(r["id"]) for r in runs}  # type: ignore[call-overload]

    if run_id_1 not in run_ids:
        raise HTTPException(status_code=404, detail=f"Run {run_id_1} not found")
    if run_id_2 not in run_ids:
        raise HTTPException(status_code=404, detail=f"Run {run_id_2} not found")

    results_1 = get_run_results(engine, run_id_1)
    results_2 = get_run_results(engine, run_id_2)

    attacks_1: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_1
    }
    attacks_2: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_2
    }

    all_attack_names = sorted(set(attacks_1) | set(attacks_2))

    entries: list[CompareEntry] = []
    for attack_name in all_attack_names:
        in_1 = attack_name in attacks_1
        in_2 = attack_name in attacks_2

        if in_1 and in_2:
            success_1 = attacks_1[attack_name]
            success_2 = attacks_2[attack_name]
            if success_1 and not success_2:
                verdict = "IMPROVED"
            elif not success_1 and success_2:
                verdict = "REGRESSED"
            else:
                verdict = "UNCHANGED"
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=success_1,
                    run_2_success=success_2,
                    verdict=verdict,
                )
            )
        elif in_1:
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=attacks_1[attack_name],
                    run_2_success=None,
                    verdict="N/A",
                )
            )
        else:
            entries.append(
                CompareEntry(
                    attack_name=attack_name,
                    run_1_success=None,
                    run_2_success=attacks_2[attack_name],
                    verdict="N/A",
                )
            )

    return entries


@app.get("/dashboard/runs", response_class=HTMLResponse)
def runs_dashboard(request: Request) -> HTMLResponse:
    """Render the runs list page."""
    engine = _get_engine()
    rows = list_runs(engine)
    runs = [
        RunSummary(
            id=int(r["id"]),  # type: ignore[call-overload]
            timestamp=r["timestamp"],  # type: ignore[arg-type]
            model=str(r["model"]),
        )
        for r in rows
    ]
    html = templates.TemplateResponse(
        request, "runs_list.html", {"runs": runs}
    )
    return html


def main() -> None:
    """Run the FastAPI app with uvicorn."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
