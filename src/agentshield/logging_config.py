"""Centralized structlog configuration for AgentShield."""

import logging

import structlog


def configure_logging(json_output: bool = False) -> None:
    """Configure structlog with human-readable or JSON output.

    Args:
        json_output: If True, use JSON rendering; otherwise use key-value.
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))



    logging.basicConfig(
    format="%(message)s",
    level=logging.INFO,
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger with the given name.

    Args:
        name: The logger name, typically ``__name__`` of the calling module.
    """
    log: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return log
