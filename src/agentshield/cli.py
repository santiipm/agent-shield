import typer

from agentshield import __version__

app = typer.Typer(
    name="agentshield",
    help="CLI tool for AI agent security evaluation.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the version of agentshield."""
    typer.echo(f"agentshield {__version__}")


@app.callback(invoke_without_command=True)
def main() -> None:
    """CLI tool for AI agent security evaluation."""
