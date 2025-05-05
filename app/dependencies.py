from fastapi import Request
from common.logging.custom_logger import get_logger
from common.logging.request_context import RequestContext


async def get_logger_with_context(request: Request):
    # Set up the context variables
    RequestContext.setup_request_context(request)
    RequestContext.on_request_start(request)

    # Ensure request_id is available in context
    from common.logging.request_context import request_id_var
    request_id_var.set(request.state.request_id)

    # Default module name
    module_name = __name__

    # Try to extract module name from request endpoint
    if (hasattr(request, "scope") and "route" in request.scope and
            hasattr(request.scope["route"], "endpoint")):
        endpoint = request.scope["route"].endpoint
        if hasattr(endpoint, "__module__"):
            module_name = endpoint.__module__

    # Get and return the logger
    logger = get_logger(module_name)
    if hasattr(request.state, "request_id"):
        logger = logger.bind_request_id(request.state.request_id)

    return logger