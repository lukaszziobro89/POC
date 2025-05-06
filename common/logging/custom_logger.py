import inspect
import logging
import os
import sys
from enum import Enum
from typing import Any, Dict

import structlog

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


class LogType(Enum):
    """Enum for log types."""
    DOMAIN = "domain"
    AUDIT = "audit"

    @classmethod
    def _missing_(cls, value: str):
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DOMAIN


def setup_logging() -> None:
    """Configure JSON-only logging for the entire application."""
    # Remove all existing handlers from the root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Configure the processors for structlog
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure standard library logging with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL)

    # Configure structlog
    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class CustomLogger:
    """Custom logger that outputs JSON formatted logs."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = structlog.get_logger(name)
        self._bound_values = {}

    def bind_request_id(self, request_id: str):
        """Bind request_id to all subsequent log calls."""
        self._bound_values["request_id"] = request_id
        return self

    def _get_caller_location(self, exc_info=None) -> Dict[str, Any]:
        """Get location information about the caller or exception."""
        # For exceptions, get the source from traceback
        if exc_info:
            try:
                tb = exc_info[2]
                if tb:
                    # Navigate to the frame where the exception occurred
                    while tb.tb_next:
                        tb = tb.tb_next

                    frame = tb.tb_frame
                    frame_info = inspect.getframeinfo(frame)
                    module = frame.f_globals.get("__name__", "unknown")
                    return {
                        "module": module,
                        "function": frame_info.function,
                        "line": frame_info.lineno
                    }
            except Exception:
                pass  # Fall back to caller info if exception handling fails

        # Get caller info from stack
        frame = inspect.currentframe()
        if frame:
            try:
                # Skip _get_caller_location, _log, and log level method frames
                caller_frame = frame
                for _ in range(3):
                    if caller_frame.f_back:
                        caller_frame = caller_frame.f_back

                if caller_frame:
                    frame_info = inspect.getframeinfo(caller_frame)
                    module = caller_frame.f_globals.get("__name__", "unknown")
                    return {
                        "module": module,
                        "function": frame_info.function,
                        "line": frame_info.lineno
                    }
            finally:
                del frame  # Clean up references

        return {"function": "unknown", "line": 0}

    def _normalize_args(self, *args, **kwargs) -> Dict[str, Any]:
        """Normalize different calling patterns to a single dict format."""
        # Start with default log data
        result = {"log_type": "domain"}

        # Handle LogType
        if args and isinstance(args[0], LogType):
            result["log_type"] = args[0].value
            args = args[1:]
        elif "log_type" in kwargs:
            log_type = kwargs.pop("log_type")
            if isinstance(log_type, LogType):
                result["log_type"] = log_type.value
            else:
                result["log_type"] = str(log_type).lower()

        # Handle message
        if args:
            result["event"] = str(args[0])
            # Additional args
            for i, arg in enumerate(args[1:], 1):
                result[f"arg{i}"] = arg
        elif "message" in kwargs:
            result["event"] = kwargs.pop("message")

        # Add remaining kwargs and bound values
        result.update(kwargs)
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
        # Get exception info if available
        exc_info = kwargs.get('exc_info', False)

        # Get caller information
        caller_info = self._get_caller_location(
            sys.exc_info() if exc_info is True else exc_info if exc_info else None
        )

        # Extract location information
        module_name = caller_info.get("module")
        function_name = caller_info.get("function")
        line_number = caller_info.get("line")

        # Normalize arguments
        normalized = self._normalize_args(*args, **kwargs)
        event = normalized.pop("event", "")

        # Add line number to log data
        if line_number:
            normalized["line"] = line_number

        # Create logger with proper module and function context
        logger_name = self.name
        if module_name and function_name:
            if self.name != module_name:  # Avoid duplicating module name
                logger_name = f"{module_name}.{function_name}"
            else:
                logger_name = f"{self.name}.{function_name}"
        elif function_name:
            logger_name = f"{self.name}.{function_name}"

        # Log with the properly contextualized logger
        return getattr(structlog.get_logger(logger_name), level)(event, **normalized)

    def debug(self, *args, **kwargs):
        return self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        return self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        return self._log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        return self._log("critical", *args, **kwargs)


def get_logger(name: str = "app") -> CustomLogger:
    """Get a custom logger instance that produces JSON-only logs."""
    return CustomLogger(name)