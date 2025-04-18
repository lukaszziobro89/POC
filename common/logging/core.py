import logging
import structlog

from common.logging.processors import GenerateEventIdProcessor
from common.logging.schemas import AUDIT_LOG_LEVEL_NUM, AUDIT_LOG_LEVEL_NAME
from common.logging.structured_logger import StructuredLogger

def setup_logging() -> None:
    logging.addLevelName(AUDIT_LOG_LEVEL_NUM, AUDIT_LOG_LEVEL_NAME)
    logging.basicConfig(level="INFO", format="%(message)s")

def setup_logger() -> logging.Logger:
    logger = StructuredLogger("PNC_LOGGER")
    logger.parent = logger.root
    logger.setLevel("INFO")
    return logger

def get_logger() -> StructuredLogger:
    setup_logging()
    logger = setup_logger()

    structlog_logger: StructuredLogger = structlog.wrap_logger(
        logger,
        wrapper_class=structlog.BoundLogger,
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="datetime"),
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.MODULE,
                ]
            ),
            GenerateEventIdProcessor
        ]
    )
    return structlog_logger