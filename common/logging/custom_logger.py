import inspect
import logging
import os
import sys
from enum import Enum
from typing import Any, Dict, Optional

import structlog

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
        wrapper_class=structlog.stdlib.BoundLogger,  # type: ignore
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

    @staticmethod
    def _get_caller_info() -> Dict[str, Any]:
        """Get information about the caller (function name and line number)."""
        caller_info = {}

        # Get the current frame and navigate up to find the caller
        frame = inspect.currentframe()
        if frame:
            try:
                # Navigate through frames to find the actual caller
                caller_frame = frame
                for _ in range(3):  # Skip _get_caller_info, _log, and log level method
                    if caller_frame.f_back:
                        caller_frame = caller_frame.f_back

                if caller_frame:
                    # Extract function name and line number
                    frame_info = inspect.getframeinfo(caller_frame)
                    caller_info["function"] = frame_info.function
                    caller_info["line"] = frame_info.lineno

                    # Add module name if available
                    if hasattr(caller_frame, "f_globals") and "__name__" in caller_frame.f_globals:
                        caller_info["module"] = caller_frame.f_globals["__name__"]
            finally:
                # Clean up frame references to avoid reference cycles
                del frame
        return caller_info

    @staticmethod
    def _get_exception_source(exc_info=None) -> Optional[Dict[str, Any]]:
        """Extract source information from exception traceback."""
        if not exc_info:
            return None

        try:
            tb = exc_info[2]
            if tb:
                # Navigate to the frame where the exception occurred
                while tb.tb_next:
                    tb = tb.tb_next

                frame = tb.tb_frame
                frame_info = inspect.getframeinfo(frame)
                result = {
                    "function": frame_info.function,
                    "line": frame_info.lineno
                }

                # Add module name if available
                if hasattr(frame, "f_globals") and "__name__" in frame.f_globals:
                    result["module"] = frame.f_globals["__name__"]

                return result
        except Exception:
            pass

        return None

    def _normalize_args(self, *args, **kwargs) -> Dict[str, Any]:
        """Normalize different calling patterns to a single dict format."""
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

        # Get exception info if available
        exc_info = kwargs.get('exc_info', False)

        # Get caller information, prioritizing exception source if available
        if level in ["error", "critical"] and exc_info:
            # For error logs with exceptions, try to get the source of the exception
            source_info = self._get_exception_source(sys.exc_info() if exc_info is True else exc_info)
            caller_info = source_info if source_info else self._get_caller_info()
        else:
            caller_info = self._get_caller_info()

        # Extract module and function name
        module_name = caller_info.pop("module", None)
        function_name = caller_info.pop("function", None)

        # Add line number to normalized data
        if "line" in caller_info:
            normalized["line"] = caller_info["line"]

        # Create a custom logger name that includes both module and function
        logger_with_function = self.logger
        if module_name and function_name:
            # If the current logger name already has module info, don't duplicate it
            if self.name != module_name:
                logger_name = f"{module_name}.{function_name}"
            else:
                logger_name = f"{self.name}.{function_name}"
            logger_with_function = structlog.get_logger(logger_name)
        elif function_name:
            logger_name = f"{self.name}.{function_name}"
            logger_with_function = structlog.get_logger(logger_name)

        # Log with structlog using the enhanced logger name
        return getattr(logger_with_function, level)(event, **normalized)

    def debug(self, *args, **kwargs):
        return self._log("debug", *args, **kwargs)

    def info(self, *args, **kwargs):
        return self._log("info", *args, **kwargs)

    def warning(self, *args, **kwargs):
        return self._log("warning", *args, **kwargs)

    def error(self, *args, **kwargs):
        # Always capture exception info for error logs if not explicitly provided
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        return self._log("error", *args, **kwargs)

    def critical(self, *args, **kwargs):
        # Always capture exception info for critical logs if not explicitly provided
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        return self._log("critical", *args, **kwargs)

def get_logger(name: str = "app") -> CustomLogger:
    """Get a custom logger instance that produces JSON-only logs."""
    return CustomLogger(name)