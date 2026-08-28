import asyncio

import typer

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


@app.callback(invoke_without_command=True)
def main() -> None:
    """CLI tool for AI agent security evaluation."""

if __name__ == "__main__":
    app()