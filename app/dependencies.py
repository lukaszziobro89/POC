from fastapi import Request
from common.logging.custom_logger import get_logger
from common.logging.request_context import RequestContext, request_id_var


async def get_logger_with_context(request: Request):
    """Set up a contextualized logger for the current request.

    This middleware:
    1. Sets up request context with request ID
    2. Creates a logger with proper module/function naming
    3. Binds request ID to the logger

    Returns:
        CustomLogger: A logger configured for the current request context
    """
    # Set up request context
    RequestContext.setup_request_context(request)
    RequestContext.on_request_start(request)

    # Ensure request_id is available in context
    if hasattr(request.state, "request_id"):
        request_id_var.set(request.state.request_id)

    # Determine the appropriate logger name from the endpoint
    logger_name = None
    if hasattr(request, "scope") and "route" in request.scope:
        endpoint = request.scope["route"].endpoint
        if hasattr(endpoint, "__module__"):
            module_name = endpoint.__module__
            if hasattr(endpoint, "__name__"):
                logger_name = f"{module_name}.{endpoint.__name__}"
            else:
                logger_name = module_name

    # Create and configure logger
    logger = get_logger(logger_name or __name__)
    if hasattr(request.state, "request_id"):
        logger = logger.bind_request_id(request.state.request_id)

    return logger