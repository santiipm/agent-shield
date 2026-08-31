from pathlib import Path
from unittest.mock import AsyncMock, patch

from typer.testing import CliRunner

from agentshield.cli import app

runner = CliRunner()


def _make_run(run_id: int, model: str = "gpt-4") -> dict[str, object]:
    """Create a mock run dictionary."""
    return {
        "id": run_id,
        "timestamp": f"2025-01-0{run_id}T10:00:00",
        "model": model,
        "json_path": f"/tmp/r{run_id}.json",
    }


def _make_result(
    attack_name: str,
    success: bool,
    category: str = "prompt_injection",
) -> dict[str, object]:
    """Create a mock attack result dictionary."""
    return {
        "attack_name": attack_name,
        "success": success,
        "attack_category": category,
        "confidence": 0.9,
        "error": None,
    }


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "agentshield" in result.output


def test_run_command_mocked(tmp_path: Path) -> None:
    """Run command completes with exit_code 0 when OllamaAgent is mocked."""
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
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.save_run", return_value=1),
    ):
        result = runner.invoke(app, ["run", "--model", "llama3.2"])

    assert result.exit_code == 0, result.output
    assert "Report saved to:" in result.output
    assert "Run persisted with id: 1" in result.output


def test_history_command_mocked() -> None:
    """History command displays runs from the database."""
    mock_runs = [_make_run(2, "llama3.2"), _make_run(1, "gpt-4")]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch(
            "agentshield.persistence.db.list_runs",
            return_value=mock_runs,
        ),
    ):
        result = runner.invoke(app, ["history"])

    assert result.exit_code == 0, result.output
    assert "Evaluation History" in result.output
    assert "llama3.2" in result.output
    assert "gpt-4" in result.output


def test_compare_command_improved() -> None:
    """Compare shows IMPROVED when attack goes vulnerable to resisted."""
    mock_runs = [_make_run(1), _make_run(2)]
    results_1 = [_make_result("injection", success=True)]
    results_2 = [_make_result("injection", success=False)]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.list_runs", return_value=mock_runs),
        patch(
            "agentshield.persistence.db.get_run_results",
            side_effect=[results_1, results_2],
        ),
    ):
        result = runner.invoke(app, ["compare", "1", "2"])

    assert result.exit_code == 0, result.output
    assert "IMPROVED" in result.output
    assert "injection" in result.output


def test_compare_command_regressed() -> None:
    """Compare shows REGRESSED when attack goes resisted to vulnerable."""
    mock_runs = [_make_run(1), _make_run(2)]
    results_1 = [_make_result("injection", success=False)]
    results_2 = [_make_result("injection", success=True)]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.list_runs", return_value=mock_runs),
        patch(
            "agentshield.persistence.db.get_run_results",
            side_effect=[results_1, results_2],
        ),
    ):
        result = runner.invoke(app, ["compare", "1", "2"])

    assert result.exit_code == 0, result.output
    assert "REGRESSED" in result.output


def test_compare_command_unchanged() -> None:
    """Compare shows UNCHANGED when attack result is identical."""
    mock_runs = [_make_run(1), _make_run(2)]
    results_1 = [_make_result("injection", success=True)]
    results_2 = [_make_result("injection", success=True)]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.list_runs", return_value=mock_runs),
        patch(
            "agentshield.persistence.db.get_run_results",
            side_effect=[results_1, results_2],
        ),
    ):
        result = runner.invoke(app, ["compare", "1", "2"])

    assert result.exit_code == 0, result.output
    assert "UNCHANGED" in result.output


def test_compare_command_na_missing_attack() -> None:
    """Compare shows N/A when attack is missing from one run."""
    mock_runs = [_make_run(1), _make_run(2)]
    results_1 = [_make_result("injection", success=True)]
    results_2 = [
        _make_result("exfiltration", success=True, category="data_exfil"),
    ]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.list_runs", return_value=mock_runs),
        patch(
            "agentshield.persistence.db.get_run_results",
            side_effect=[results_1, results_2],
        ),
    ):
        result = runner.invoke(app, ["compare", "1", "2"])

    assert result.exit_code == 0, result.output
    assert "N/A" in result.output
    assert "injection" in result.output
    assert "exfiltration" in result.output


def test_compare_command_mixed_scenarios() -> None:
    """Compare handles mixed improved/regressed/unchanged/na scenarios."""
    mock_runs = [_make_run(1), _make_run(2)]
    results_1 = [
        _make_result("improved_attack", success=True, category="cat1"),
        _make_result("regressed_attack", success=False, category="cat2"),
        _make_result("unchanged_attack", success=True, category="cat3"),
        _make_result("only_in_run1", success=True, category="cat4"),
    ]
    results_2 = [
        _make_result("improved_attack", success=False, category="cat1"),
        _make_result("regressed_attack", success=True, category="cat2"),
        _make_result("unchanged_attack", success=True, category="cat3"),
        _make_result("only_in_run2", success=False, category="cat5"),
    ]

    with (
        patch("agentshield.persistence.db.get_engine"),
        patch("agentshield.persistence.db.init_db"),
        patch("agentshield.persistence.db.list_runs", return_value=mock_runs),
        patch(
            "agentshield.persistence.db.get_run_results",
            side_effect=[results_1, results_2],
        ),
    ):
        result = runner.invoke(app, ["compare", "1", "2"])

    assert result.exit_code == 0, result.output
    assert "IMPROVED" in result.output
    assert "REGRESSED" in result.output
    assert "UNCHANGED" in result.output
    assert "N/A" in result.output
