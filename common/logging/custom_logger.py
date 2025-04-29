import logging
import os
import sys
from enum import Enum
from typing import Any, Dict

import structlog

# Configuration
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


class LogType(Enum):
    """Enum for log types."""

    DOMAIN = "domain"
    AUDIT = "audit"

    @classmethod
    def _missing_(cls, value: str):
        """Handle string values for log_type."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DOMAIN


def setup_logging() -> None:
    """Configure JSON-only logging for the entire application.
    This ensures ALL logs (application, library, and uvicorn) are in JSON format.
    """
    # Remove all existing handlers from the root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Configure the processors for structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)

    # This creates a custom formatter that passes the event dict directly to JSONRenderer
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
        keep_exc_info=False,
        keep_stack_info=False,
    )

    # Setting formatter, handler and log level
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)

    # Configure structlog to pass its output through standard library logging
    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger, # type: ignore
        cache_logger_on_first_use=True,
    )


class CustomLogger:
    """Custom logger that outputs JSON formatted logs. All logs will be consistently formatted as JSON."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = structlog.get_logger(name)
        self._bound_values = {}

    def bind_request_id(self, request_id: str):
        """Bind request_id to all subsequent log calls."""
        self._bound_values["request_id"] = request_id
        return self

    def _normalize_args(self, *args, **kwargs) -> Dict[str, Any]:
        """Normalize different calling patterns to a single dict format.
        Handles all the various ways our logging methods might be called."""

        # Start with default log type
        result = {"log_type": "domain"}

        # First, check if first arg is LogType
        if args and isinstance(args[0], LogType):
            result["log_type"] = args[0].value
            args = args[1:]  # Remove LogType from args

        # Handle explicit log_type in kwargs
        elif "log_type" in kwargs:
            log_type = kwargs.pop("log_type")
            if isinstance(log_type, LogType):
                result["log_type"] = log_type.value
            else:
                result["log_type"] = str(log_type).lower()

        # Handle message from args or kwargs
        if args:
            result["event"] = str(args[0])
            # Additional args
            for i, arg in enumerate(args[1:], 1):
                result[f"arg{i}"] = arg
        elif "message" in kwargs:
            result["event"] = kwargs.pop("message")

        # Add the rest of kwargs
        result.update(kwargs)

        # Add bound values if not overridden
        for key, value in self._bound_values.items():
            if key not in result:
                result[key] = value

        # Add request_id from context if not already present
        from common.logging.request_context import request_id_var

        request_id = request_id_var.get(None)
        if request_id is not None and "request_id" not in result:
            result["request_id"] = request_id

        return result

    def _log(self, level: str, *args, **kwargs):
        """Internal method to handle all logging with consistent formatting."""
        normalized = self._normalize_args(*args, **kwargs)

        # Extract event message if present, otherwise use an empty string
        event = normalized.pop("event", "")

        # Log with structlog
        return getattr(self.logger, level)(event, **normalized)

    def debug(self, *args, **kwargs):
        return self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        return self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        return self._log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        return self._log("critical", *args, **kwargs)


def get_logger(name: str = "app") -> CustomLogger:
    """Get a custom logger instance that produces JSON-only logs."""
    return CustomLogger(name)
