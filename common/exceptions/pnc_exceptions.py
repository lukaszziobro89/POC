# common/pnc_exceptions.py
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from common.logging.custom_logger import get_logger

logger = get_logger(__name__)


class PncException(Exception):
    """Base exception for application-specific errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OcrException(PncException):
    """Exception raised for OCR-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


class ClassificationException(PncException):
    """Exception raised for classification-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


class VolumeException(PncException):
    """Exception raised for volume-related errors."""

    def __init__(self, message: str, status_code: int = 422):
        super().__init__(message, status_code)


def setup_exception_handlers(app: FastAPI):
    """Set up global exception handlers for the application."""

    def log_exception(request: Request, exc: Exception, status_code: int):
        """Helper function to log exceptions."""
        req_logger = getattr(request.state, "logger", logger)
        req_logger.error(
            "Request failed",
            error=getattr(exc, "message", str(exc)),
            status_code=status_code,
            exception_type=type(exc).__name__
        )

    @app.exception_handler(PncException)
    async def pnc_exception_handler(request: Request, exc: PncException):
        log_exception(request, exc, exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.message, "status_code": exc.status_code}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        log_exception(request, exc, 500)
        return JSONResponse(
            status_code=500,
            content={"message": str(exc), "status_code": 500}
        )