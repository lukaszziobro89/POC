import contextvars
import time
import uuid
from typing import Optional

from fastapi import Request

from common.logging.custom_logger import get_logger

# Define request_id_var at module level for global access
request_id_var = contextvars.ContextVar("request_id", default=None)


class RequestContext:
    """Utility class for handling request context and logging.

    This class:
    1. Generates or extracts request IDs (if required)
    2. Creates request-specific loggers
    3. Provides timing utilities
    4. Handles request context management
    """

    REQUEST_ID_PATH_PARAM = "requestId"
    REQUEST_ID_ENDPOINTS = ["/request"]
    NON_REQUEST_ID_ENDPOINTS = ["/token", "/healthcheck"]

    @staticmethod
    def generate_request_id() -> str:
        """Generate a new request ID with a date prefix."""
        return f"{time.strftime('%Y%m%d', time.gmtime())}#{uuid.uuid4()}"

    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Get the client IP address from the request."""
        pass

    @staticmethod
    def setup_request_context(request: Request, request_id: Optional[str] = None) -> None:
        """Set up a request context with an appropriate request ID and logger.

        Request ID handling strategies:
        1. For /request endpoint: Generate a new request ID
        2. For other endpoints (except /token and /healthcheck):
           Extract request ID from path parameter {requestId}
        3. For /token and /healthcheck: Skip request ID handling

        Args:
        ----
            request: The FastAPI request object
            request_id: Optional request ID to use (overrides automatic handling)
        """
        path = request.url.path

        # Use the calling module's name instead of a path for logger
        import inspect

        caller_frame = inspect.currentframe().f_back
        module_name = caller_frame.f_globals["__name__"]

        # Skip request ID handling for specific endpoints
        if path in RequestContext.NON_REQUEST_ID_ENDPOINTS:
            # Only set up logger without request ID
            logger = get_logger(path)
            request.state.logger = logger
            request.state.start_time = time.time()
            return

        # Use provided request ID if available
        if request_id is None:
            if path == RequestContext.REQUEST_ID_ENDPOINTS:
                # Generate new request ID for /request endpoint
                request_id = RequestContext.generate_request_id()
            else:
                # Extract request ID from path parameter for other endpoints
                # Get the requestId from path parameters
                path_params = request.path_params
                request_id = path_params.get(RequestContext.REQUEST_ID_PATH_PARAM)
                if not request_id:
                    # Fallback to generated ID if not found in path
                    request_id = RequestContext.generate_request_id()

        # Bind request ID to current context
        request_id_var.set(request_id)
        request.state.request_id = request_id

        # Create and bind logger
        logger = get_logger(module_name)
        request.state.logger = logger.bind_request_id(request_id)


    @staticmethod
    def on_request_start(request: Request) -> None:
        """Actions to perform at the start of a request."""
        pass

    @staticmethod
    def on_request_end(request: Request, status_code=int) -> None:
        """Actions to perform at the end of a request."""
        pass

    @staticmethod
    def on_request_error(request: Request, error: Exception) -> None:
        """Log request error details."""
        request.state.logger.error(
            "Request processing failed",
            request_id=request.state.request_id,
            error=str(error),
            exception_type=type(error).__name__,
        )
