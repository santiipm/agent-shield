from typer.testing import CliRunner

from agentshield.cli import app

runner = CliRunner()


def test_version_command() -> None:

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "agentshield" in result.output
