"""
📊 TruthGPT Cloud - Structured Cloud Logging (Powered by Structlog)
Provides enterprise structured JSON and console logging for distributed tracing,
audit metrics, request context binding, and telemetry.
"""

import sys
import logging
from typing import Any, Dict, Optional

_HAS_STRUCTLOG = False
try:
    import structlog
    _HAS_STRUCTLOG = True
except ImportError:
    _HAS_STRUCTLOG = False


class _FallbackLogger:
    """Fallback logger that mimics structlog's API using standard library logging."""

    def __init__(self, std_logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        self._logger = std_logger
        self._context: Dict[str, Any] = context or {}

    def bind(self, **new_values: Any) -> "_FallbackLogger":
        merged = {**self._context, **new_values}
        return _FallbackLogger(self._logger, merged)

    def unbind(self, *keys: str) -> "_FallbackLogger":
        merged = {k: v for k, v in self._context.items() if k not in keys}
        return _FallbackLogger(self._logger, merged)

    def _format_msg(self, event: str, kw: Dict[str, Any]) -> str:
        all_kw = {**self._context, **kw}
        if not all_kw:
            return event
        parts = [f"{k}={v!r}" for k, v in all_kw.items()]
        return f"{event} | " + " ".join(parts)

    def debug(self, event: str, **kw: Any) -> None:
        self._logger.debug(self._format_msg(event, kw))

    def info(self, event: str, **kw: Any) -> None:
        self._logger.info(self._format_msg(event, kw))

    def warning(self, event: str, **kw: Any) -> None:
        self._logger.warning(self._format_msg(event, kw))

    def error(self, event: str, **kw: Any) -> None:
        self._logger.error(self._format_msg(event, kw))

    def critical(self, event: str, **kw: Any) -> None:
        self._logger.critical(self._format_msg(event, kw))

    def exception(self, event: str, **kw: Any) -> None:
        self._logger.exception(self._format_msg(event, kw))


def configure_logging(
    json_format: bool = False,
    log_level: str = "INFO",
    log_format: Optional[str] = None,
) -> None:
    """
    Configure global structured logging with Structlog.
    If json_format is True or log_format=="json", outputs machine-readable JSON lines for Datadog / ELK / Loki.
    If json_format is False, outputs colored developer-friendly console output.
    """
    if log_format is not None:
        json_format = (log_format.lower() == "json")

    lvl = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=lvl,
    )

    if not _HAS_STRUCTLOG:
        return

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors + [renderer],
        wrapper_class=structlog.make_filtering_bound_logger(lvl),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "truthgpt_cloud", **bound_context: Any) -> Any:
    """
    Obtain a structured logger for TruthGPT Cloud.
    Returns a structlog BoundLogger if structlog is available, otherwise returns
    a compatible fallback logger wrapping logging.Logger.
    """
    if _HAS_STRUCTLOG:
        base = structlog.get_logger(name)
        if bound_context:
            return base.bind(**bound_context)
        return base
    std_logger = logging.getLogger(name)
    return _FallbackLogger(std_logger, context=bound_context)


def bind_context(**kwargs: Any) -> None:
    """Bind global contextual variables (e.g. user_id, tier, request_id) for the current task."""
    if _HAS_STRUCTLOG and hasattr(structlog, "contextvars"):
        structlog.contextvars.bind_contextvars(**kwargs)


def unbind_context(*keys: str) -> None:
    """Unbind global contextual variables for the current task."""
    if _HAS_STRUCTLOG and hasattr(structlog, "contextvars"):
        structlog.contextvars.unbind_contextvars(*keys)


get_cloud_logger = get_logger
configure_structured_logging = configure_logging

__all__ = [
    "_HAS_STRUCTLOG",
    "configure_logging",
    "configure_structured_logging",
    "get_logger",
    "get_cloud_logger",
    "bind_context",
    "unbind_context",
]
