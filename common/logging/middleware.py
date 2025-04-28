import time
import uuid
import contextvars
from typing import Callable
from fastapi import Request, Response, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


from common.logging.custom_logger import get_logger, DatadogHttpHandler

# Define request_id_var at module level for global access
request_id_var = contextvars.ContextVar("request_id", default=None)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and binding request ID.

    This middleware:
    1. Generates a unique request ID for each request
    2. Binds the request ID to the request state
    3. Creates a request-specific logger
    4. Logs request details including timing, client info, and status code
    5. Handles exceptions during request processing
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process an incoming request, add logging, and handle errors.
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler in the chain
        Returns: The HTTP response
        """
        # Generate request ID with date prefix for easier log filtering
        # Use module-level ContextVar for global access across the application
        request_id = f"{time.strftime('%Y%m%d', time.gmtime())}#{uuid.uuid4()}"

        # Bind request ID to current context
        request_id_var.set(request_id)
        request.state.request_id = request_id
        request.state.logger = get_logger(request.url.path).bind_request_id(request_id)

        # Log request start
        start_time = time.time()

        # Get client IP address with proper handling for proxies
        client_ip = self._get_client_ip(request)

        # Get client type from User-Agent
        client = request.headers.get("User-Agent", "unknown")

        # Logging request received
        request.state.logger.audit(
            "HTTP Request Received",
            path=request.url.path,
            base_url=str(request.base_url),
            client=client,
            client_ip_address=client_ip,
            x_forwarded_for=request.headers.get("X-Forwarded-For"),
            httpmethod=request.method
        )

        # Process the request
        try:
            # Call the next middleware or route handler
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Log error and create an error response
            request.state.logger.error(
                "Request processing failed",
                error=str(e),
                exception_type=type(e).__name__
            )
            status_code = 500
            response = Response(content="Internal Server Error", status_code=status_code)
        finally:
            # Log request completion as audit log
            process_time = time.time() - start_time
            request.state.logger.audit(
                "HTTP Request Completed",
                path=request.url.path,
                base_url=str(request.base_url),
                client=client,
                client_ip_address=client_ip,
                x_forwarded_for=request.headers.get("X-Forwarded-For"),
                httpmethod=request.method,
                status_code=status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
        return response

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract the client IP address from the request, handling proxies correctly.
        Args:
            request: The HTTP request
        Returns:
            The client IP address
        """
        # Start with the direct client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check for X-Forwarded-For header (common in proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # The leftmost IP is the original client
            client_ip = forwarded_for.split(",")[0].strip()

        return client_ip


# def setup_logging(app: FastAPI) -> FastAPI:
#     """Set up logging for a FastAPI application.
#     This function adds the RequestLoggingMiddleware to the application.
#     Args:
#         app: The FastAPI application
#     Returns:
#         The configured FastAPI application
#     """
#     # Add request logging middleware
#     app.add_middleware(RequestLoggingMiddleware)
#
#     # Return the configured app
#     return app
# In setup_logging() function (common/logging/middleware.py)
import structlog
from logging import StreamHandler, FileHandler
# from common.logging.datadog_handler import DatadogHttpHandler

DATADOG_API_KEY = "3a4c85a2b3ed8695598f93513ad38465"
DATADOG_SITE = "datadoghq.eu"
import logging

def setup_logging(app: FastAPI) -> FastAPI:
    """Set up logging for a FastAPI application.
    This function adds the RequestLoggingMiddleware to the application and configures logging handlers.
    Args:
        app: The FastAPI application
    Returns:
        The configured FastAPI application
    """
    # Create handlers
    stream_handler = StreamHandler()
    datadog_handler = DatadogHttpHandler(DATADOG_API_KEY, DATADOG_SITE)

    # Configure standard library logging first
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[stream_handler, datadog_handler]
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set formatting for all handlers
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
    )

    # Apply formatter to all handlers
    stream_handler.setFormatter(formatter)
    datadog_handler.setFormatter(formatter)

    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    return app