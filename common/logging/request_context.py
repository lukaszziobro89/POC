import contextvars
import time
import uuid
import inspect
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

        # Skip request ID handling for specific endpoints
        if path in RequestContext.NON_REQUEST_ID_ENDPOINTS:
            # Only set up logger without request ID
            logger = get_logger(path)
            request.state.logger = logger
            request.state.start_time = time.time()
            return

        # Use provided request ID if available
        if request_id is None:
            if path in RequestContext.REQUEST_ID_ENDPOINTS:
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

        # Try to extract module and function name from request endpoint
        module_name = None
        function_name = None

        if (hasattr(request, "scope") and "route" in request.scope and
                hasattr(request.scope["route"], "endpoint")):
            endpoint = request.scope["route"].endpoint
            if hasattr(endpoint, "__module__"):
                module_name = endpoint.__module__
            if hasattr(endpoint, "__name__"):
                function_name = endpoint.__name__

        # If we couldn't get module_name from endpoint, try to get it from caller
        if not module_name:
            frame = inspect.currentframe()
            if frame and frame.f_back:
                module_name = frame.f_back.f_globals["__name__"]

        # Create the logger name that includes both module and function if available
        logger_name = module_name or "app"
        if function_name:
            logger_name = f"{logger_name}.{function_name}"

        # Create and bind logger
        logger = get_logger(logger_name)
        request.state.logger = logger.bind_request_id(request_id)
        request.state.start_time = time.time()

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
        # Extract the exception location information
        tb = error.__traceback__
        while tb.tb_next:
            tb = tb.tb_next

        frame = tb.tb_frame
        code = frame.f_code

        # Get the correct module and function name from the exception
        module_name = frame.f_globals.get("__name__", "unknown")
        function_name = code.co_name

        # Create a properly formatted logger name
        logger_name = f"{module_name}.{function_name}"

        # Use the module-specific logger
        logger = get_logger(logger_name).bind_request_id(request.state.request_id)

        logger.error(
            "Request processing failed",
            error=str(error),
            exception_type=type(error).__name__,
        )