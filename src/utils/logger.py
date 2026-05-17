
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)

logger = logging.getLogger("webhook-engine")


def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)


def log_warn(msg):
    logger.warning(msg)
