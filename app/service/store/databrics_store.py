import random
from time import sleep

from common.logging.custom_logger import LogType, get_logger

from config import MIN_VOLUME_TIME, MAX_VOLUME_TIME

def perform_volume() -> None:
    logger = get_logger(__name__)
    logger.info(log_type=LogType.AUDIT, message=">>> ATTEMPTING TO PERFORM VOLUME <<<")
    logger.info("Performing volume...")
    random_volume_time = random.randint(MIN_VOLUME_TIME, MAX_VOLUME_TIME)
    logger.info(f"random_volume_time={random_volume_time}")
    sleep(random_volume_time)
    logger.info("VOLUME completed successfully", result="sample_result")
