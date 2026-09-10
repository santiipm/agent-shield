"""Tests for the logging configuration module."""

import structlog

from agentshield.logging_config import configure_logging, get_logger


def test_configure_logging_human_readable() -> None:
    """configure_logging() completes without error for default mode."""
    configure_logging(json_output=False)
    assert structlog.is_configured()


def test_configure_logging_json() -> None:
    """configure_logging(json_output=True) completes without error."""
    configure_logging(json_output=True)
    assert structlog.is_configured()


def test_configure_logging_idempotent() -> None:
    """Calling configure_logging multiple times does not raise."""
    configure_logging(json_output=False)
    configure_logging(json_output=True)
    configure_logging(json_output=False)
    assert structlog.is_configured()


def test_get_logger_returns_usable_logger() -> None:
    """get_logger returns a logger that supports standard log methods."""
    configure_logging(json_output=False)
    log = get_logger("test_module")
    log.info("test_event", key="value")
    log.warning("test_warning", count=42)
    log.error("test_error", detail="something went wrong")
    log.debug("test_debug", flag=True)


def test_get_logger_json_mode() -> None:
    """get_logger works after configuring JSON output."""
    configure_logging(json_output=True)
    log = get_logger("test_json_module")
    log.info("json_event", data=123)
