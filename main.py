# main.py
import logging
from fastapi import FastAPI

# Import our custom logger
from common.logging.middleware import setup_logging
from common.logging.custom_logger import get_logger

# Import routers
from app.routers import base, items
import requests

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


DATADOG_API_KEY = "3a4c85a2b3ed8695598f93513ad38465"
DATADOG_SITE = "datadoghq.eu"

# Add to your app startup code
def verify_datadog_connection():
    try:
        response = requests.get(
            f"https://api.{DATADOG_SITE}/api/v1/validate",
            headers={"DD-API-KEY": DATADOG_API_KEY},
            timeout=5
        )
        if response.status_code == 200:
            print("✓ Datadog connection verified")
        else:
            print(f"⚠️ Datadog API key validation failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Cannot connect to Datadog: {e}")

# Call this during app startup
verify_datadog_connection()

if __name__ == "__main__":
    import uvicorn
    from uvicorn_log_config import LOGGING_CONFIG
    verify_datadog_connection()

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
