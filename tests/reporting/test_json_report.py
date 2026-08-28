"""Tests for JSON report generation."""

import json
from pathlib import Path

from agentshield.core.result import AttackResult
from agentshield.reporting.json_report import save_report


def test_save_report_creates_file(tmp_path: Path) -> None:
    """Report file is created and contains valid JSON."""
    results = [
        AttackResult(
            attack_name="test_attack",
            attack_category="test",
            turns=["turn1"],
            responses=["response1"],
            success=True,
            confidence=0.95,
            evidence="Found keyword",
        )
    ]

    file_path = save_report(results, output_dir=str(tmp_path))

    assert Path(file_path).exists()


def test_save_report_returns_correct_path(tmp_path: Path) -> None:
    """Returned path points to the created file under output_dir."""
    results = [
        AttackResult(
            attack_name="a",
            attack_category="c",
            turns=[],
            responses=[],
            success=False,
            confidence=1.0,
            evidence="none",
        )
    ]

    file_path = save_report(results, output_dir=str(tmp_path))

    assert file_path.startswith(str(tmp_path))
    assert file_path.endswith(".json")


def test_save_report_json_roundtrip(tmp_path: Path) -> None:
    """Data written to JSON can be parsed back and matches the original."""
    results = [
        AttackResult(
            attack_name="injection",
            attack_category="prompt_injection",
            turns=["ignore instructions"],
            responses=["I cannot do that."],
            success=False,
            confidence=1.0,
            evidence="Target phrase not found",
        ),
        AttackResult(
            attack_name="exfiltration",
            attack_category="data_exfil",
            turns=["send data"],
            responses=["Here is the data: secret"],
            success=True,
            confidence=0.8,
            evidence="Found secret in response",
        ),
    ]

    file_path = save_report(results, output_dir=str(tmp_path))

    loaded = json.loads(Path(file_path).read_text())
    assert len(loaded) == 2
    assert loaded[0]["attack_name"] == "injection"
    assert loaded[1]["success"] is True
    assert loaded[1]["confidence"] == 0.8


def test_save_report_empty_list(tmp_path: Path) -> None:
    """Empty results list produces a valid JSON array."""
    file_path = save_report([], output_dir=str(tmp_path))

    loaded = json.loads(Path(file_path).read_text())
    assert loaded == []


def test_save_report_creates_nested_dir(tmp_path: Path) -> None:
    """output_dir is created recursively if it doesn't exist."""
    nested = tmp_path / "a" / "b" / "c"
    file_path = save_report([], output_dir=str(nested))

    assert Path(file_path).exists()
    assert str(nested) in file_path
