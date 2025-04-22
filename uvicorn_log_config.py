# uvicorn_log_config.py
"""
Uvicorn logging configuration.

This module configures Uvicorn's logging to work well with our custom logging setup.
It disables Uvicorn's access logs (since we have our own audit logs) and sets
appropriate log levels for Uvicorn's error logs.
"""
import os

# Get log level from environment or default to WARNING for Uvicorn
UVICORN_LOG_LEVEL = os.environ.get("UVICORN_LOG_LEVEL", "WARNING").upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": "structlog.processors.JSONRenderer",
        },
    },
    "handlers": {
        "default": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": UVICORN_LOG_LEVEL},
        "uvicorn.error": {"handlers": ["default"], "level": UVICORN_LOG_LEVEL, "propagate": False},
        "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
    },
}
