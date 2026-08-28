"""Console report renderer for attack results."""

from rich.console import Console
from rich.table import Table

from agentshield.core.result import AttackResult


def print_summary(results: list[AttackResult]) -> None:
    """Print a formatted summary table of attack results to the console.

    Args:
        results: List of attack results to display.
    """
    console = Console()
    table = Table(title="Attack Results Summary")

    table.add_column("Attack", style="bold")
    table.add_column("Category")
    table.add_column("Result")
    table.add_column("Confidence")

    for result in results:
        if result.error:
            result_text = "[yellow]ERROR[/yellow]"
            confidence_text = "-"
        elif result.success:
            result_text = "[red]VULNERABLE[/red]"
            confidence_text = f"{int(result.confidence * 100)}%"
        else:
            result_text = "[green]RESISTED[/green]"
            confidence_text = f"{int(result.confidence * 100)}%"

        table.add_row(
            result.attack_name,
            result.attack_category,
            result_text,
            confidence_text,
        )

    console.print(table)
