from fastapi import Request, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi import Depends
from app.dependencies import get_logger_with_context
from common.exceptions.pnc_exceptions import Error, PncException

def setup_exception_handlers(app: FastAPI, logger=Depends(get_logger_with_context)):
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


    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Convert FastAPI/Pydantic validation errors to PncException."""

        error_details = []
        for error in exc.errors():
            location = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{location}: {message}")

        error_message = f"Bad request: {'; '.join(error_details)}"
        log_exception(request, exc, 400)
        return Error(400, error_message).to_response()

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle all unspecified exceptions with a generic error response."""
        log_exception(request, exc, 500)
        return Error(getattr(exc, "status_code", 500), str(exc)).to_response()

