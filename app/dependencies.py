from fastapi import Request

async def get_request_logger(request: Request):
    """Dependency to get the logger with request ID."""
    return request.state.logger