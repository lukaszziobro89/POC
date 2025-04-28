"""Uvicorn logging configuration to ensure JSON output.
This configuration must be in sync with custom_logger.py to ensure consistent formatting.
"""

import os

import structlog

# Configuration
UVICORN_LOG_LEVEL = os.environ.get("UVICORN_LOG_LEVEL", "INFO").upper()

# Configure shared processors for consistent formatting with application logs
shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
]

# JSON-only logging configuration for uvicorn
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": shared_processors,
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "level": UVICORN_LOG_LEVEL,
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": UVICORN_LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": UVICORN_LOG_LEVEL,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["default"],
            "level": UVICORN_LOG_LEVEL,
            "propagate": False,
        },
    },
}
