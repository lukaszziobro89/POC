from common.logging.custom_logger import get_logger
from typing import Optional

def perform_ocr() -> None:
    logger = get_logger(__name__)
    logger.info("Performing OCR...")
    logger.info("OCR completed successfully", result="sample_result")
