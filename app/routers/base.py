from fastapi import APIRouter, Request, Depends
from common.logging.custom_logger import get_logger
from app.service.ocr import azure_ai_vision
from app.dependencies import get_request_logger

# Get a logger for this module
logger = get_logger("routers.base")

# Create a router
router = APIRouter(tags=["base"])

@router.get("/")
async def root(logger=Depends(get_request_logger)):
    logger.info("Root endpoint accessed")
    return {"message": "Hello World"}

@router.get("/ocr")
async def ocr(logger=Depends(get_request_logger)):
    logger.info("preparing OCR")
    azure_ai_vision.perform_ocr()
    logger.info("OCR DONE!")
    return {"status": "success", "message": "OCR completed"}
