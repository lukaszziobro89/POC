from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_logger_with_context
from app.service.classification.classify import perform_classification
from app.service.ocr import azure_ai_vision
from common.exceptions.pnc_exceptions import PncException, ClassificationException, OcrException
from common.logging.request_context import RequestContext

router = APIRouter(tags=["base"])


@router.get("/")
async def root(request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info("Root endpoint accessed")
        return {"message": "Hello World"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)


@router.get("/request")
async def create_request(request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info("Creating new request")
        request_id = request.state.request_id
        logger.info(f"Request created with ID: {request_id}")
        logger.error(f"Request creation failed!")
        raise Exception('Some exception occurred')
        # raise ValueError('Some exception occurred')
        # raise PncException(status_code=500, message='Some exception occurred')
    # except PncException as e:
    #     raise
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail="Here i got internal server error !")
    finally:
        RequestContext.on_request_end(request, 200)

@router.get("/request/{requestId}")
async def create_request(request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info("Creating new request")
        request_id = request.state.request_id
        logger.info(f"Request created with ID: {request_id}")
        raise ClassificationException('Some exception occurred')
        return {"request_id": request_id, "status": "created"}
    # except ClassificationException as e:
    #     raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)

@router.get("/ocr")
async def ocr_endpoint(request: Request, logger=Depends(get_logger_with_context)):

    try:
        logger.info("preparing OCR")
        azure_ai_vision.perform_ocr()
        logger.info("OCR DONE!")
        return {"status": "success", "message": "OCR completed"}
    except OcrException as e:
        raise
    finally:
        RequestContext.on_request_end(request, 500)


@router.get("/classify/{requestId}")
async def classify(requestId: str, request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info(f"preparing CLASSIFICATION for request ID: {requestId}")
        perform_classification()
        logger.info(f"CLASSIFICATION DONE for request ID: {requestId}!")
        return {
            "status": "success",
            "message": f"CLASSIFICATION completed for request ID: {requestId}",
        }
    except ClassificationException as e:
        raise
    finally:
        RequestContext.on_request_end(request, 500)


from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional
from common.exceptions.pnc_exceptions import PncException, RequestStoreException


class ExtractionData(BaseModel):
    document_type: str = Field(..., description="Type of document to extract")
    content_areas: list[str] = Field(..., description="Areas to extract content from")
    options: Optional[Dict[str, Any]] = Field(default={}, description="Additional extraction options")


@router.post("/extraction/{requestId}")
async def extract_content(
        requestId: str,
        request: Request,
        extraction_data: ExtractionData,
        logger=Depends(get_logger_with_context)
):
    try:
        logger.info(f"Starting extraction for request ID: {requestId}")
        # Perform extraction logic here using validated extraction_data
        logger.info(extraction_data)

        logger.info(f"Extraction completed for request ID: {requestId}")
        return {
            "status": "success",
            "request_id": requestId,
            "message": "Extraction completed successfully"
        }
    except Exception as e:
        # Only handle business logic errors here, not validation errors
        raise PncException(message=f"Extraction failed: {str(e)}", status_code=422)
    finally:
        RequestContext.on_request_end(request, 200)

@router.get("/token")
async def token(request: Request, logger=Depends(get_logger_with_context)):
    logger.info("Token endpoint accessed")
    return {"token": "sample-token"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}
