"""
Structured logging configuration for the application.

This module provides a custom logger implementation that combines domain and audit logging
using structlog. It supports request ID binding, caller information tracking, and
environment-based configuration.
"""
import contextvars
import structlog
import inspect
import logging
import sys
import os
from typing import Dict, Any, Optional

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
NUMERIC_LOG_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)


# First, set up Python's standard logging module with a StreamHandler to output to stdout
# We'll configure the root logger later after setting up the JSON formatter

def rename_event_to_message(_logger, _method_name, event_dict):
    """Rename the 'event' key to 'message' for compatibility with various log consumers.
    Args:
        _logger: The logger instance (unused)
        _method_name: The logging method name (unused)
        event_dict: The log event dictionary
    Returns:
        The modified event dictionary
    """
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict


# Configure structlog
structlog.configure(
    processors=[
        rename_event_to_message,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Set up the formatter for standard library integration
formatter = structlog.stdlib.ProcessorFormatter(
    processor=structlog.processors.JSONRenderer(),
)

# Create a single handler for our custom logs
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
handler.setLevel(NUMERIC_LOG_LEVEL)

# Configure the root logger to use JSON formatting
root_logger = logging.getLogger()
root_logger.handlers = [handler]  # Replace any existing handlers
root_logger.setLevel(NUMERIC_LOG_LEVEL)

# Create a logger specifically for our application
app_logger = logging.getLogger("GenAI_P&C")
app_logger.setLevel(NUMERIC_LOG_LEVEL)
app_logger.handlers = [handler]  # Replace any existing handlers
app_logger.propagate = False  # Don't propagate to root logger

# Disable Uvicorn's access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").propagate = False


class CustomLogger:
    """Custom logger class that combines domain and audit logging. This class provides a unified interface
    for both domain and audit logging, with support for request ID binding, caller information tracking, and
    structured logging.
    Attributes:
        domain_logger: The structlog logger for domain logs
        audit_logger: The structlog logger for audit logs
        request_id: The current request ID, if any
        _caller_info_cache: Cache for caller information to improve performance
    """

    def __init__(self, name: str):
        """Initialize a new CustomLogger instance.
        Args:
            name: The logger name, typically the module name or path
        """
        # Normalize the name to ensure consistent naming
        normalized_name = self._normalize_name(name)

        # Create both domain and audit loggers with our namespace
        self.domain_logger = structlog.get_logger(f"app.{normalized_name}.domain")
        self.audit_logger = structlog.get_logger(f"app.{normalized_name}.audit")
        self.request_id = None
        self._caller_info_cache = {}

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize the logger name to ensure consistent naming.
        Args:
            name: The original logger name
        Returns: The normalized logger name
        """
        # Remove 'app.' prefix if present to avoid duplication
        if name.startswith("app."):
            name = name[4:]

        # Replace URL paths with normalized names
        if name.startswith("/"):
            # Convert URL paths to dot notation and remove leading/trailing slashes
            name = name.strip("/").replace("/", ".")

        return name

    def bind_request_id(self, request_id: str) -> "CustomLogger":
        """Bind a request ID to both loggers.
        Args:
            request_id: The request ID to bind
        Returns: The logger instance for method chaining
        """
        self.request_id = request_id
        self.domain_logger = self.domain_logger.bind(request_id=request_id)
        self.audit_logger = self.audit_logger.bind(request_id=request_id)
        return self

    def _get_caller_info(self) -> Dict[str, Any]:
        """Get the caller's module, function name, and line number. This looks up the call stack to find the actual
        caller (skipping internal logger methods). Uses caching to improve performance for repeated calls
        from the same location.
        Returns: A dictionary containing module, func_name, and lineno
        """
        try:
            # Start with the immediate caller
            frame = inspect.currentframe()
            if not frame:
                return self._default_caller_info()

            # Move up to the method that called _log_domain
            frame = frame.f_back  # Move to _log_domain
            if not frame:
                return self._default_caller_info()

            # Move up to the actual logger method (info, debug, etc.)
            frame = frame.f_back  # Move to debug/info/etc.
            if not frame:
                return self._default_caller_info()

            # Move up to the actual application code
            frame = frame.f_back  # Move to the actual caller
            if not frame:
                return self._default_caller_info()

            # Get a cache key based on the frame's code object and line number
            # This allows us to cache caller info for repeated calls from the same location
            cache_key = (id(frame.f_code), frame.f_lineno)

            # Check if we have this information cached
            if cache_key in self._caller_info_cache:
                return self._caller_info_cache[cache_key]

            # Extract the information
            module = inspect.getmodule(frame)
            module_name = module.__name__ if module else "unknown"
            func_name = frame.f_code.co_name
            lineno = frame.f_lineno

            # Cache and return the result
            result = {
                "module": module_name,
                "func_name": func_name,
                "lineno": lineno
            }
            self._caller_info_cache[cache_key] = result
            return result

        except Exception:
            # If anything goes wrong, return default values
            return self._default_caller_info()
        finally:
            # Ensure we clean up any frame references to avoid memory leaks
            del frame

    @staticmethod
    def _default_caller_info() -> Dict[str, Any]:
        """Return default caller information when actual info cannot be determined.
        Returns: A dictionary with default caller information
        """
        return {
            "module": "unknown",
            "func_name": "unknown",
            "lineno": 0
        }

    def _log_domain(self, level: str, message: str, **kwargs) -> None:
        """Log a domain message with caller information.
        Args:
            level: The log level (debug, info, warning, error, critical)
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        caller_info = self._get_caller_info()
        log_method = getattr(self.domain_logger, level)
        log_method(
            message,
            log_type="domain",
            **caller_info,
            **kwargs
        )

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self._log_domain("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self._log_domain("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self._log_domain("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self._log_domain("error", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self._log_domain("critical", message, **kwargs)

    def audit(self, message: str, **kwargs) -> None:
        """Log an audit message.
        Args:
            message: The log message
            **kwargs: Additional key-value pairs to include in the log
        """
        self.audit_logger.info(
            message,
            log_type="audit",
            **kwargs
        )


# Add at the top of custom_logger.py
import contextvars


def get_logger(name: str, request_id: Optional[str] = None) -> CustomLogger:
    """Get a custom logger instance.
    Args:
        name: The logger name
        request_id: Optional request ID to automatically bind
    Returns:
        A configured CustomLogger instance
    """
    logger = CustomLogger(name)

    # Use provided request_id if available
    if request_id:
        logger = logger.bind_request_id(request_id)
    else:
        # Try to get request_id from context variable
        try:
            # Import inside function to avoid circular import
            from common.logging.middleware import request_id_var
            ctx_request_id = request_id_var.get()
            if ctx_request_id:
                logger = logger.bind_request_id(ctx_request_id)
        except (LookupError, ImportError):
            # No request ID in context or import issue
            pass

    return logger
