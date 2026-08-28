from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from agentshield.cli import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "agentshield" in result.output


def test_run_command_mocked(tmp_path: Path) -> None:
    """Run command completes with exit_code 0 when OllamaAgent is mocked."""
    mock_response = AsyncMock()
    mock_response.return_value = "nothing happened"

    mock_invoke = AsyncMock(return_value="nothing happened")

    with (
        patch(
            "agentshield.agents.ollama_agent.OllamaAgent.invoke",
            mock_invoke,
        ),
        patch(
            "agentshield.reporting.json_report.save_report",
            return_value=str(tmp_path / "run_test.json"),
        ),
    ):
        result = runner.invoke(app, ["run", "--model", "llama3.2"])

    assert result.exit_code == 0, result.output
    assert "Report saved to:" in result.output
