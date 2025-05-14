import random
from time import sleep

from common.exceptions.handlers import OcrException, PncException
from common.logging.custom_logger import LogType, get_logger
from config import MIN_OCR_TIME, MAX_OCR_TIME


def perform_ocr() -> None:
    logger = get_logger(__name__)
    logger.error(">>> LOGGER ERROR<<<")
    raise PncException('OCR failed', status_code=424)
    # raise OcrException('OCR failed', status_code=422)
    logger.info(log_type=LogType.AUDIT, message=">>> ATTEMPTING TO PERFORM OCR <<<")
    logger.info("Performing OCR...")
    random_ocr_time = random.randint(MIN_OCR_TIME, MAX_OCR_TIME)
    logger.info(f"random_ocr_time={random_ocr_time}")
    sleep(random_ocr_time)
    logger.info("OCR completed successfully", result="sample_result")
