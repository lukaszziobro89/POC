from fastapi import FastAPI, Request, Response
from starlette.responses import JSONResponse

from app.routers import base
from common.exceptions.pnc_exceptions import setup_exception_handlers
from common.logging.custom_logger import get_logger, setup_logging
import uvicorn
from uvicorn_log_config import LOGGING_CONFIG

# Setup logging before anything else
setup_logging()

# Create FastAPI app
app = FastAPI(title="MyAPI")

# Get a logger for this module
logger = get_logger(__name__)

# Include routers
app.include_router(base.router)
setup_exception_handlers(app)

if __name__ == "__main__":

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
