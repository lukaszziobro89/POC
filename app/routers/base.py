from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import get_logger_with_context
from app.service.classification.classify import perform_classification
from app.service.ocr import azure_ai_vision
from common.logging.request_context import RequestContext

router = APIRouter(tags=["base"])


@router.get("/")
async def root(request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info("Root endpoint accessed")
        return {"message": "Hello World"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
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
        raise HTTPException(status_code=500, detail="Some exception occurred.")
        return {"request_id": request_id, "status": "created"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)

@router.get("/request/{requestId}")
async def create_request(request: Request, logger=Depends(get_logger_with_context)):
    try:
        logger.info("Creating new request")
        request_id = request.state.request_id
        logger.info(f"Request created with ID: {request_id}")
        return {"request_id": request_id, "status": "created"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 200)

@router.get("/ocr")
async def ocr_endpoint(request: Request, logger=Depends(get_logger_with_context)):

    try:
        logger.info("preparing OCR")
        azure_ai_vision.perform_ocr()
        logger.info("OCR DONE!")
        return {"status": "success", "message": "OCR completed"}
    except Exception as e:
        RequestContext.on_request_error(request, e)
        response_status = 500
        raise HTTPException(status_code=response_status, detail="Internal server error")
    finally:
        RequestContext.on_request_end(request, 500)


@router.get("/classify/{requestId}")
async def classify(requestId: str, request: Request, logger=Depends(get_logger_with_context)):
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
async def token(request: Request, logger=Depends(get_logger_with_context)):
    logger.info("Token endpoint accessed")
    return {"token": "sample-token"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}
