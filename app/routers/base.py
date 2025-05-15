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
        return {"request_id": request_id, "status": "created"}
    except Exception as e:
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


@router.get("/token")
async def token(request: Request, logger=Depends(get_logger_with_context)):
    logger.info("Token endpoint accessed")
    return {"token": "sample-token"}


@router.get("/healthcheck")
async def healthcheck():
    return {"status": "healthy"}
