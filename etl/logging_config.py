import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_PATH, LOG_LEVEL

_LOGGING_CONFIGURED = False


def setup_logging() -> logging.Logger:
    """Configure and return the project-level logger.

    Uses RotatingFileHandler to prevent unbounded log growth.
    Called once at import time. Subsequent calls are no-ops.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return logging.getLogger("etl_project")

    log_dir = os.path.dirname(LOG_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    logger = logging.getLogger("etl_project")
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    _LOGGING_CONFIGURED = True
    return logger


logger = setup_logging()
