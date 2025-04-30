from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import (
    get_request_logger,
    process_request_logging,
)
from app.service.classification.classify import perform_classification
from app.service.ocr import azure_ai_vision
from common.logging.custom_logger import get_logger
from common.logging.request_context import RequestContext

router = APIRouter(tags=["base"])

logger = get_logger(__name__)


@router.get("/", dependencies=[Depends(process_request_logging)])
async def root(request: Request, logger=Depends(get_request_logger)):
    try:
        logger.info("Root endpoint accessed 2")
        return {"message": "Hello World"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)


@router.get("/request", dependencies=[Depends(process_request_logging)])
async def create_request(request: Request, logger=Depends(get_request_logger)):
    try:
        logger.info("Creating new request")
        # Extract request ID that was generated in the dependency
        request_id = request.state.request_id
        logger.info(f"Request created with ID: {request_id}")
        return {"request_id": request_id, "status": "created"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)


@router.get("/request/{requestId}", dependencies=[Depends(process_request_logging)])
async def create_request(
    request: Request, requestId: str, logger=Depends(get_request_logger),
):
    try:
        logger.info("Creating new request")
        # Extract request ID that was generated in the dependency
        request_id = request.state.request_id
        logger.info(f"Request created with ID: {request_id}")
        return {"request_id": request_id, "status": "created"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)


@router.get("/ocr")
async def ocr(request: Request, logger=Depends(get_request_logger)):

    # For endpoints without request ID in path and not excluded
    RequestContext.setup_request_context(request)
    RequestContext.on_request_start(request)

    try:
        logger.info("preparing OCR")
        azure_ai_vision.perform_ocr()
        logger.info("OCR DONE!")
        response_status = 200
        return {"status": "success", "message": "OCR completed"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        response_status = 500
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 500)


@router.get("/classify/{requestId}", dependencies=[Depends(process_request_logging)])
async def classify(requestId: str, request: Request, logger=Depends(get_request_logger)):
    try:
        logger.info(f"preparing CLASSIFICATION for request ID: {requestId}")
        perform_classification()
        logger.info(f"CLASSIFICATION DONE for request ID: {requestId}!")
        response_status = 200
        return {
            "status": "success",
            "message": f"CLASSIFICATION completed for request ID: {requestId}",
        }
    except Exception as e:
        RequestContext.on_request_error(request, e)
        response_status = 500
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 500)


@router.get("/token")
async def token(request: Request):
    logger.info("Token endpoint accessed")
    return {"token": "sample-token"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}
