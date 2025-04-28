from fastapi import FastAPI, Request, Response

from app.routers import base, items
from common.logging.custom_logger import get_logger, setup_logging

# Setup logging before anything else
setup_logging()

# Create FastAPI app
app = FastAPI(title="MyAPI")

# Get a logger for this module
logger = get_logger(__name__)

# Include routers
app.include_router(base.router)
# app.include_router(items.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure all errors are properly logged."""
    if hasattr(request.state, "logger"):
        request.state.logger.error(
            "Unhandled exception", error=str(exc), exception_type=type(exc).__name__,
        )
    else:
        logger.error(
            "Unhandled exception", error=str(exc), exception_type=type(exc).__name__,
        )
    return Response(content="Internal Server Error", status_code=500)


if __name__ == "__main__":
    import uvicorn

    from uvicorn_log_config import LOGGING_CONFIG  # Make sure this path is correct

    # Log application initialization
    # logger.info("Application initialized successfully!")
    # Run uvicorn with our JSON logging configuration
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_config=LOGGING_CONFIG,
        reload=True,
        access_log=False,
    )
