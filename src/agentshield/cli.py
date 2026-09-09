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
    from agentshield.persistence.db import get_engine, init_db, save_run
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

    engine = get_engine("agentshield.db")
    init_db(engine)
    run_id = save_run(engine, model, report_path, all_results)
    typer.echo(f"Run persisted with id: {run_id}")


@app.command()
def history() -> None:
    """List past evaluation runs."""
    from agentshield.persistence.db import get_engine, init_db, list_runs

    engine = get_engine("agentshield.db")
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
    from agentshield.persistence.db import get_engine, get_run_results, init_db

    engine = get_engine("agentshield.db")
    init_db(engine)

    results_1 = get_run_results(engine, run_id_1)
    results_2 = get_run_results(engine, run_id_2)

    attacks_1: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_1
    }
    attacks_2: dict[str, bool] = {
        str(r["attack_name"]): bool(r["success"]) for r in results_2
    }

    all_attack_names = sorted(set(attacks_1) | set(attacks_2))

    console = Console()
    table = Table(title=f"Comparison: Run {run_id_1} vs Run {run_id_2}")
    table.add_column("Attack", style="bold")
    table.add_column(f"Run {run_id_1}")
    table.add_column(f"Run {run_id_2}")
    table.add_column("Verdict")

    for attack_name in all_attack_names:
        in_1 = attack_name in attacks_1
        in_2 = attack_name in attacks_2

        if in_1 and in_2:
            success_1 = attacks_1[attack_name]
            success_2 = attacks_2[attack_name]
            col_1 = "VULNERABLE" if success_1 else "RESISTED"
            col_2 = "VULNERABLE" if success_2 else "RESISTED"

            if success_1 and not success_2:
                verdict = "[green]IMPROVED[/green]"
            elif not success_1 and success_2:
                verdict = "[red]REGRESSED[/red]"
            else:
                verdict = "UNCHANGED"
        elif in_1:
            success_1 = attacks_1[attack_name]
            col_1 = "VULNERABLE" if success_1 else "RESISTED"
            col_2 = "N/A"
            verdict = "[yellow]N/A[/yellow]"
        else:
            col_1 = "N/A"
            success_2 = attacks_2[attack_name]
            col_2 = "VULNERABLE" if success_2 else "RESISTED"
            verdict = "[yellow]N/A[/yellow]"

        table.add_row(attack_name, col_1, col_2, verdict)

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
