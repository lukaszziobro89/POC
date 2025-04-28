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
    "filters": {
        "domain": {
            "()": "common.logging.custom_logger.DomainLogTypeFilter",  # Replace with your actual filter path
        }
    },
    "handlers": {
        "default": {
            "formatter": "json",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["domain"],
        },
        "datadog": {
            "formatter": "json",
            "class": "common.logging.custom_logger.DatadogHttpHandler",  # Replace with your actual path
            "api_key": "3a4c85a2b3ed8695598f93513ad38465",
            "site": "datadoghq.eu",
            "filters": ["domain"],
        }
    },
    "loggers": {
        "uvicorn": {"handlers": ["default", "datadog"], "level": UVICORN_LOG_LEVEL},
        "uvicorn.error": {"handlers": ["default", "datadog"], "level": UVICORN_LOG_LEVEL, "propagate": False},
        "uvicorn.access": {"handlers": [], "level": "WARNING", "propagate": False},
        # Add your application loggers
        "your_app": {"handlers": ["default", "datadog"], "level": "INFO", "propagate": False},
    },
}