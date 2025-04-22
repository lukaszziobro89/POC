# main.py
import logging
from fastapi import FastAPI

# Import our custom logger
from common.logging.middleware import setup_logging
from common.logging.custom_logger import get_logger

# Import routers
from app.routers import base, items

# Configure logging before creating the app
# Disable uvicorn access logs since we have our own audit logs
logging.getLogger("uvicorn.access").disabled = True

# Create FastAPI app
app = FastAPI(title="MyAPI")

# Setup logging - this needs to happen BEFORE any logging occurs
app = setup_logging(app)

# Get a logger for this module
logger = get_logger("main")

# Include routers
app.include_router(base.router)
app.include_router(items.router)


if __name__ == "__main__":
    import uvicorn
    from uvicorn_log_config import LOGGING_CONFIG

    logger.info("P&C Application initialized successfully!")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        proxy_headers=True,
        forwarded_allow_ips='*',
        log_config=LOGGING_CONFIG,
        reload=True,
    )
