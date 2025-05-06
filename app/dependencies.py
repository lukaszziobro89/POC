from fastapi import Request
import inspect
from common.logging.custom_logger import get_logger
from common.logging.request_context import RequestContext


async def get_logger_with_context(request: Request):
    # Set up the context variables
    RequestContext.setup_request_context(request)
    RequestContext.on_request_start(request)

    # Ensure request_id is available in context
    from common.logging.request_context import request_id_var
    request_id_var.set(request.state.request_id)

    # Try to extract module name from request endpoint
    module_name = __name__
    function_name = None

    if (hasattr(request, "scope") and "route" in request.scope and
            hasattr(request.scope["route"], "endpoint")):
        endpoint = request.scope["route"].endpoint
        if hasattr(endpoint, "__module__"):
            module_name = endpoint.__module__

        # Extract the function name from the endpoint
        if hasattr(endpoint, "__name__"):
            function_name = endpoint.__name__

    # Create the correct logger name that includes both module and function
    logger_name = module_name
    if function_name:
        logger_name = f"{module_name}.{function_name}"

    # Get the logger with the full path
    logger = get_logger(logger_name)

    # Bind request_id if available
    if hasattr(request.state, "request_id"):
        logger = logger.bind_request_id(request.state.request_id)

    return logger