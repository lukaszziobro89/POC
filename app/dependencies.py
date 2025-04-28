# app/dependencies.py
import uuid

from fastapi import Request

from common.logging.custom_logger import get_logger
from common.logging.request_context import RequestContext


# In app/dependencies.py
def process_request_logging(request: Request) -> None:
    """Set up request context and logging for all regular endpoints."""
    # Generate and set request_id if not already present
    if not hasattr(request.state, "request_id"):
        request.state.request_id = str(uuid.uuid4())

    # Set up the context variables
    RequestContext.setup_request_context(request)
    RequestContext.on_request_start(request)

    # Ensure request_id is available in context
    from common.logging.request_context import request_id_var

    request_id_var.set(request.state.request_id)


def get_request_id_from_path(request: Request) -> str:
    """Extract request ID from path parameters."""
    return request.path_params.get("requestId")


# In dependencies.py
def process_request_with_id_from_path(request: Request) -> None:
    """Setup request context using path parameter request ID and log request start.
    Used as a dependency for endpoints that receive a request ID in the path.
    """
    request_id = request.path_params.get("requestId")
    if request_id:
        # Set up request context with provided request ID
        RequestContext.setup_request_context(request, request_id)

        # Log request start
        RequestContext.on_request_start(request)



def process_request_with_id(request: Request, request_id: str) -> None:
    """Setup request context using path parameter request ID and log request start.
    Used as a dependency for endpoints that receive a request ID.
    """
    # Set up request context with provided request ID
    RequestContext.setup_request_context(request, request_id)

    # Log request start
    RequestContext.on_request_start(request)



# In app/dependencies.py
def get_request_logger(request: Request):
    """Get a logger with request_id bound to it."""
    # Use the calling module name instead of the URL path
    if hasattr(request, "scope") and "route" in request.scope:
        if hasattr(request.scope["route"], "endpoint"):
            endpoint = request.scope["route"].endpoint
            if hasattr(endpoint, "__module__"):
                module_name = endpoint.__module__

    logger = get_logger(module_name)

    # Explicitly bind the request_id from request.state
    if hasattr(request.state, "request_id"):
        logger = logger.bind_request_id(request.state.request_id)
    return logger
