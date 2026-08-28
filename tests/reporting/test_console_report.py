"""Tests for console report rendering."""

import contextlib
import io

from agentshield.core.result import AttackResult
from agentshield.reporting.console_report import print_summary


def _make_result(
    *,
    success: bool,
    error: str | None = None,
    confidence: float = 1.0,
    name: str = "attack",
    category: str = "cat",
) -> AttackResult:
    return AttackResult(
        attack_name=name,
        attack_category=category,
        turns=["t"],
        responses=["r"],
        success=success,
        confidence=confidence,
        evidence="ev",
        error=error,
    )


def test_print_summary_runs_without_error() -> None:
    """print_summary completes without raising."""
    results = [
        _make_result(success=True),
        _make_result(success=False),
        _make_result(success=False, error="timeout"),
    ]
    print_summary(results)


def test_print_summary_vulnerable_in_output() -> None:
    """Captured output contains VULNERABLE for a successful attack."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [_make_result(success=True, name="inj", category="prompt")]
        print_summary(results)

    output = buf.getvalue()
    assert "VULNERABLE" in output


def test_print_summary_resisted_in_output() -> None:
    """Captured output contains RESISTED for a resisted attack."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [_make_result(success=False, name="def", category="defense")]
        print_summary(results)

    output = buf.getvalue()
    assert "RESISTED" in output


def test_print_summary_error_in_output() -> None:
    """Captured output contains ERROR for an errored attack."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [
            _make_result(success=False, error="something broke", name="fail")
        ]
        print_summary(results)

    output = buf.getvalue()
    assert "ERROR" in output


def test_print_summary_confidence_percentage() -> None:
    """Confidence is shown as a percentage."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [_make_result(success=True, confidence=0.75)]
        print_summary(results)

    output = buf.getvalue()
    assert "75%" in output


def test_print_summary_error_confidence_dash() -> None:
    """Error results show '-' for confidence."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [
            _make_result(success=False, error="err", confidence=0.5)
        ]
        print_summary(results)

    output = buf.getvalue()
    assert "-" in output


def test_print_summary_mixed_results() -> None:
    """Mixed results render correctly together."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = [
            _make_result(success=True, name="vuln", confidence=1.0),
            _make_result(success=False, name="res", confidence=0.9),
            _make_result(success=False, error="timeout", name="err"),
        ]
        print_summary(results)

    output = buf.getvalue()
    assert "VULNERABLE" in output
    assert "RESISTED" in output
    assert "ERROR" in output
    assert "100%" in output
    assert "90%" in output


def test_print_summary_empty_list() -> None:
    """Empty results list renders without error."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print_summary([])

    output = buf.getvalue()
    assert "Attack" in output
