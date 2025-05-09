import threading
import time
import requests
from requests.exceptions import JSONDecodeError
import uvicorn
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional

from common.logging.custom_logger import get_logger, setup_logging, LogType

setup_logging()

logger = get_logger("example_app")

items = {
    1: {"name": "Item 1", "description": "This is the first item"},
    2: {"name": "Item 2", "description": "This is the second item"},
    3: {"name": "Item 3", "description": "This is the third item"},
}

app = FastAPI(title="Example FastAPI Application")


@app.get("/")
async def root():
    """Root endpoint that returns a welcome message."""
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Example FastAPI Application"}


@app.get("/items/")
async def get_all_items():
    """Get all items."""
    logger.info("Getting all items", log_type=LogType.DOMAIN)
    return items


@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Get a specific item by ID."""
    logger.info(f"Getting item with ID: {item_id}", item_id=item_id)

    if item_id not in items:
        logger.error(f"Item with ID {item_id} not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    return items[item_id]


@app.post("/items/")
async def create_item(name: str, description: Optional[str] = None):
    """Create a new item."""
    logger.info("Creating new item", item_name=name)

    # Generate a new ID
    new_id = max(items.keys()) + 1 if items else 1

    # Create new item
    items[new_id] = {"name": name, "description": description}

    logger.info("Item created successfully", item_id=new_id, item_name=name)
    return items[new_id]


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item by ID."""
    logger.info("Attempting to delete item", item_id=item_id)

    if item_id not in items:
        logger.error("Item not found for deletion", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    deleted_item = items.pop(item_id)
    logger.info("Item deleted successfully", item_id=item_id, item_name=deleted_item['name'])

    return {"status": "success", "message": f"Item {item_id} deleted"}


@app.get("/random-error")
async def random_error():
    """Endpoint that randomly succeeds or fails."""
    logger.info("Random error endpoint accessed")

    # Always raise error for demonstration purposes
    logger.error("Random error occurred")
    raise HTTPException(status_code=500, detail="Random error occurred")


@app.get("/audit-example")
async def audit_example():
    """Example of audit logging."""
    logger.info(LogType.AUDIT, "User action recorded", action="view_sensitive_data", user_id="example123")
    return {"status": "success", "message": "Audit log created"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions and log them."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}",
                 status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")


def safe_response_content(response):
    try:
        return response.json()
    except JSONDecodeError:
        return response.text[:100] + "..." if len(response.text) > 100 else response.text


def make_requests():
    base_url = "http://127.0.0.1:8000"

    time.sleep(3)

    try:
        logger.info("Starting to make HTTP requests")

        # GET Root endpoint
        logger.info("Making request to root endpoint")
        response = requests.get(f"{base_url}/")
        logger.info(f"Root endpoint response: {response.status_code} {safe_response_content(response)}")

        # GET all items
        logger.info("Making request to get all items")
        response = requests.get(f"{base_url}/items/")
        logger.info(f"Get all items response: {response.status_code} {safe_response_content(response)}")

        # GET a specific item
        logger.info("Making request to get item 1")
        response = requests.get(f"{base_url}/items/1")
        logger.info(f"Get item 1 response: {response.status_code} {safe_response_content(response)}")

        # GET a non-existent item (will cause an error)
        logger.info("Making request to get non-existent item")
        response = requests.get(f"{base_url}/items/999")
        logger.info(f"Get non-existent item response: {response.status_code} {safe_response_content(response)}")

        # POST create a new item
        logger.info("Making request to create a new item")
        response = requests.post(f"{base_url}/items/?name=New%20Item&description=A%20newly%20created%20item")
        logger.info(f"Create item response: {response.status_code} {safe_response_content(response)}")

        # DELETE an item
        logger.info("Making request to delete an item")
        response = requests.delete(f"{base_url}/items/2")
        logger.info(f"Delete item response: {response.status_code} {safe_response_content(response)}")

        # GET the audit example
        logger.info("Making request to audit example")
        response = requests.get(f"{base_url}/audit-example")
        logger.info(f"Audit example response: {response.status_code} {safe_response_content(response)}")

        # GET the random error endpoint
        logger.info("Making request to random error endpoint")
        response = requests.get(f"{base_url}/random-error")
        logger.info(f"Random error response: {response.status_code} {safe_response_content(response)}")

        logger.info("Completed all HTTP requests")

    except Exception as e:
        logger.error(f"Error during tests: {str(e)}")
    finally:
        time.sleep(1)
        logger.info("Shutting down the application")
        sys.exit(0)


if __name__ == "__main__":
    try:
        logger.info("Starting FastAPI example application")

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        make_requests()

    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)