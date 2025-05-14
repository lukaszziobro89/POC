from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

from common.exceptions.handlers import ClassificationException, Error, OcrException, VolumeException, PncException
from common.logging.custom_logger import get_logger

logger = get_logger(__name__)

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
        """Handle PncException errors."""
        log_exception(request, exc, exc.status_code)
        return Error(exc.status_code, exc.message).to_response()

    @app.exception_handler(OcrException)
    async def ocr_exception_handler(request: Request, exc: OcrException):
        """Handle OcrException errors."""
        log_exception(request, exc, exc.status_code)
        return Error(exc.status_code, exc.message).to_response()

    @app.exception_handler(ClassificationException)
    async def classification_exception_handler(request: Request, exc: ClassificationException):
        """Handle ClassificationException errors."""
        log_exception(request, exc, exc.status_code)
        return Error(exc.status_code, exc.message).to_response()

    @app.exception_handler(VolumeException)
    async def volume_exception_handler(request: Request, exc: VolumeException):
        """Handle VolumeException errors."""
        log_exception(request, exc, exc.status_code)
        return Error(exc.status_code, exc.message).to_response()

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all unspecified exceptions with a generic error response."""
        log_exception(request, exc, 500)
        return JSONResponse(
            status_code=getattr(exc, "status_code", 500),
            content={"message": str(exc)}
        )
