import asyncio

import typer
from rich.console import Console
from rich.table import Table

from agentshield import __version__
from agentshield.core.attack import Attack
from agentshield.core.evaluator import Evaluator
from agentshield.core.result import AttackResult

app = typer.Typer(
    name="agentshield",
    help="CLI tool for AI agent security evaluation.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the version of agentshield."""
    typer.echo(f"agentshield {__version__}")


@app.command()
def run(
    model: str = typer.Option(..., help="Ollama model name to use for attacks"),
) -> None:
    """Run all prompt injection attacks against the specified model."""
    from agentshield.logging_config import configure_logging

    configure_logging()
    asyncio.run(_run_attacks(model))


async def _run_attacks(model: str) -> None:
    """Execute all attacks against the given model and report results."""
    from agentshield.agents.ollama_agent import OllamaAgent
    from agentshield.attacks.prompt_injection.fake_system_message import (
        FakeSystemMessageAttack,
    )
    from agentshield.attacks.prompt_injection.ignore_instructions import (
        IgnoreInstructionsAttack,
    )
    from agentshield.attacks.prompt_injection.role_override import RoleOverrideAttack
    from agentshield.core.runner import Runner
    from agentshield.evaluators.keyword_evaluator import KeywordEvaluator
    from agentshield.persistence.db import (
        get_engine,
        init_db,
        resolve_db_path,
        save_run,
    )
    from agentshield.reporting.console_report import print_summary
    from agentshield.reporting.json_report import save_report

    agent = OllamaAgent(model=model)

    # Each attack may have a different target_phrase, so we pair each
    # attack with its own evaluator and run the Runner once per attack
    # (list of one). This avoids needing to change Runner's interface.
    default_phrase = "AGENTSHIELD INJECTION SUCCESSFUL"

    attacks_and_evaluators: list[tuple[Attack, Evaluator]] = [
        (IgnoreInstructionsAttack(), KeywordEvaluator(default_phrase)),
        (RoleOverrideAttack(), KeywordEvaluator(default_phrase)),
        (FakeSystemMessageAttack(), KeywordEvaluator(default_phrase)),
    ]

    runner = Runner()
    all_results: list[AttackResult] = []

    for attack, evaluator in attacks_and_evaluators:
        results = await runner.run(agent, [attack], evaluator)
        all_results.extend(results)

    print_summary(all_results)
    report_path = save_report(all_results)
    typer.echo(f"Report saved to: {report_path}")

    engine = get_engine(resolve_db_path())
    init_db(engine)
    run_id = save_run(engine, model, report_path, all_results)
    typer.echo(f"Run persisted with id: {run_id}")


@app.command()
def history() -> None:
    """List past evaluation runs."""
    from agentshield.persistence.db import (
        get_engine,
        init_db,
        list_runs,
        resolve_db_path,
    )

    engine = get_engine(resolve_db_path())
    init_db(engine)
    runs = list_runs(engine)

    console = Console()
    table = Table(title="Evaluation History")
    table.add_column("Run ID", style="bold")
    table.add_column("Timestamp")
    table.add_column("Model")

    for run in runs:
        table.add_row(
            str(run["id"]),
            str(run["timestamp"]),
            str(run["model"]),
        )

    console.print(table)


@app.command()
def compare(
    run_id_1: int = typer.Argument(..., help="First run ID to compare"),
    run_id_2: int = typer.Argument(..., help="Second run ID to compare"),
) -> None:
    """Compare two runs by attack, showing improvements/regressions."""
    from agentshield.compare import compare_runs
    from agentshield.persistence.db import (
        get_engine,
        get_run_results,
        init_db,
        resolve_db_path,
    )

    engine = get_engine(resolve_db_path())
    init_db(engine)

    results_1 = get_run_results(engine, run_id_1)
    results_2 = get_run_results(engine, run_id_2)

    entries = compare_runs(results_1, results_2)

    console = Console()
    table = Table(title=f"Comparison: Run {run_id_1} vs Run {run_id_2}")
    table.add_column("Attack", style="bold")
    table.add_column(f"Run {run_id_1}")
    table.add_column(f"Run {run_id_2}")
    table.add_column("Verdict")

    for entry in entries:
        col_1 = "VULNERABLE" if entry.run_1_success else "RESISTED"
        col_2 = "VULNERABLE" if entry.run_2_success else "RESISTED"

        if entry.run_1_success is None:
            col_1 = "N/A"
        if entry.run_2_success is None:
            col_2 = "N/A"

        verdict = entry.verdict
        if verdict == "IMPROVED":
            verdict_display = "[green]IMPROVED[/green]"
        elif verdict == "REGRESSED":
            verdict_display = "[red]REGRESSED[/red]"
        elif verdict == "N/A":
            verdict_display = "[yellow]N/A[/yellow]"
        else:
            verdict_display = verdict

        table.add_row(entry.attack_name, col_1, col_2, verdict_display)

    console.print(table)


@app.command()
def serve() -> None:
    """Start the read-only API server on http://127.0.0.1:8000."""
    from agentshield.api.app import main as api_main

    api_main()


@app.callback(invoke_without_command=True)
def main() -> None:
    """CLI tool for AI agent security evaluation."""

if __name__ == "__main__":
    app()
