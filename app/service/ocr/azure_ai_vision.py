
from common.logging.custom_logger import LogType, get_logger


def perform_ocr() -> None:
    logger = get_logger(__name__)
    logger.info(log_type=LogType.AUDIT, message=">>> ATTEMPTING TO PERFORM OCR <<<")
    logger.info("Performing OCR...")
    logger.info("OCR completed successfully", result="sample_result")
