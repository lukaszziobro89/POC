from fastapi import APIRouter, Request, Depends, HTTPException
from typing import List
from common.logging.custom_logger import get_logger
from app.dependencies import get_request_logger
from app.models import Item
from app.database import items_db

# Get a logger for this module
logger = get_logger("routers.items")

# Create a router
router = APIRouter(
    prefix="/items",
    tags=["items"],
)

@router.get("/", response_model=List[Item])
async def get_items(request: Request, logger=Depends(get_request_logger)):
    logger.info("Getting all items", item_count=len(items_db))
    return items_db

@router.post("/", response_model=Item, status_code=201)
async def create_item(item: Item, request: Request, logger=Depends(get_request_logger)):
    logger.info("Creating new item", item_name=item.name)

    # Simulate some business logic
    if any(existing_item.name == item.name for existing_item in items_db):
        logger.warning("Item with this name already exists", item_name=item.name)
        raise HTTPException(status_code=400, detail="Item with this name already exists")

    # Add the item to our "database"
    items_db.append(item)

    logger.info("Item created successfully", item_id=len(items_db) - 1)
    return item

@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int, request: Request, logger=Depends(get_request_logger)):
    logger.info("Getting item by ID", item_id=item_id)

    # Validate item_id
    if item_id < 0 or item_id >= len(items_db):
        logger.error("Item not found", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    logger.info("Item retrieved successfully", item_name=items_db[item_id].name)
    return items_db[item_id]

@router.delete("/{item_id}")
async def delete_item(item_id: int, request: Request, logger=Depends(get_request_logger)):
    logger.info("Attempting to delete item", item_id=item_id)

    # Validate item_id
    if item_id < 0 or item_id >= len(items_db):
        logger.error("Item not found for deletion", item_id=item_id)
        raise HTTPException(status_code=404, detail="Item not found")

    # For audit purposes, log who is deleting what
    deleted_item = items_db[item_id]
    logger.audit(
        "Item deleted",
        item_id=item_id,
        item_name=deleted_item.name,
        user_id=request.headers.get("X-User-ID", "unknown")
    )

    # Remove the item
    items_db.pop(item_id)

    logger.info("Item deleted successfully")
    return {"status": "success", "message": "Item deleted"}
