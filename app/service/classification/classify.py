import random
from time import sleep

from common.exceptions.pnc_exceptions import PncException
from common.exceptions.handlers import ClassificationException
from common.logging.custom_logger import LogType, get_logger

from config import MIN_CLASSIFICATION_TIME, MAX_CLASSIFICATION_TIME

def perform_classification() -> None:
    logger = get_logger(__name__)
    logger.info(log_type=LogType.AUDIT, message=">>> ATTEMPTING TO PERFORM CLASSIFICATION <<<")
    logger.info("Performing classification...")
    # raise PncException('Classification failed', status_code=422)
    raise ClassificationException('Classification failed', status_code=422)
    random_classification_time = random.randint(MIN_CLASSIFICATION_TIME, MAX_CLASSIFICATION_TIME)
    logger.info(f"random_classification_time={random_classification_time}")
    sleep(random_classification_time)
    logger.info("CLASSIFICATION completed successfully", result="sample_result")
