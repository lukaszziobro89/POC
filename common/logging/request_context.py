import contextvars
import time
import uuid
from typing import Optional

from fastapi import Request

from common.logging.custom_logger import get_logger

# Define request_id context variable
request_id_var = contextvars.ContextVar("request_id", default=None)


class RequestContext:
    """Utility class for handling request context and logging."""

    REQUEST_ID_PATH_PARAM = "requestId"
    REQUEST_ID_ENDPOINTS = ["/request"]
    NON_REQUEST_ID_ENDPOINTS = ["/token", "/healthcheck"]

    @staticmethod
    def generate_request_id() -> str:
        """Generate a new request ID with a date prefix."""
        return f"{time.strftime('%Y%m%d', time.gmtime())}#{uuid.uuid4()}"

    @staticmethod
    def setup_request_context(request: Request, request_id: Optional[str] = None) -> None:
        """Set up request context with request ID and logger."""
        path = request.url.path

        # Initialize request timing
        request.state.start_time = time.time()

        # Skip request ID handling for specific endpoints
        if path in RequestContext.NON_REQUEST_ID_ENDPOINTS:
            logger = get_logger(path)
            request.state.logger = logger
            return

        # Determine request ID
        if request_id is None:
            if path in RequestContext.REQUEST_ID_ENDPOINTS:
                # Generate new request ID for /request endpoint
                request_id = RequestContext.generate_request_id()
            else:
                # Extract request ID from path parameter or generate new one
                request_id = request.path_params.get(RequestContext.REQUEST_ID_PATH_PARAM,
                                                     RequestContext.generate_request_id())

        # Set request ID in context
        request_id_var.set(request_id)
        request.state.request_id = request_id

        # Determine logger name based on endpoint
        logger_name = None
        if hasattr(request, "scope") and "route" in request.scope:
            endpoint = request.scope["route"].endpoint
            if hasattr(endpoint, "__module__"):
                module_name = endpoint.__module__
                if hasattr(endpoint, "__name__"):
                    logger_name = f"{module_name}.{endpoint.__name__}"
                else:
                    logger_name = module_name

        # Create logger with request ID
        logger = get_logger(logger_name or "app").bind_request_id(request_id)
        request.state.logger = logger

    @staticmethod
    def on_request_start(request: Request) -> None:
        """Actions to perform at the start of a request."""
        pass  # Add implementation if needed

    @staticmethod
    def on_request_end(request: Request, status_code: int) -> None:
        """Actions to perform at the end of a request."""
        pass  # Add implementation if needed

    @staticmethod
    def on_request_error(request: Request, error: Exception) -> None:
        """Log request error details."""
        # The CustomLogger will automatically extract the correct module and function
        # from the exception traceback, so we can use the request's logger directly
        request.state.logger.error(
            "Request processing failed",
            status_code = getattr(error, "status_code", 500),
            error=getattr(error, "message", str(error)),
            exception_type=type(error).__name__,
        )