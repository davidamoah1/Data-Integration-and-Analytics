import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from config import LOG_LEVEL
from shared.context import correlation_id, request_id

_LOGGING_CONFIGURED = False


class _ContextFilter(logging.Filter):
    """Inject request/correlation IDs from context vars into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get() or "-"
        record.correlation_id = correlation_id.get() or "-"
        return True


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter with request/correlation IDs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> logging.Logger:
    """Configure and return the project-level logger.

    Uses RotatingFileHandler to prevent unbounded log growth when a writable
    LOG_PATH is configured; otherwise logs to stdout only (default for
    serverless/readonly filesystems).

    Called once at import time. Subsequent calls are no-ops.
    """
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return logging.getLogger("etl_project")

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    use_json = os.getenv("LOG_FORMAT", "text").lower() == "json"

    if use_json:
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(request_id)s - %(message)s")

    logger = logging.getLogger("etl_project")
    logger.setLevel(level)

    # Console handler is always safe (serverless-friendly)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    console_handler.addFilter(_ContextFilter())
    logger.addHandler(console_handler)

    # Optional file handler â€” only when LOG_PATH is explicitly configured and writable
    log_path = os.getenv("LOG_PATH", "").strip()
    if log_path:
        try:
            log_dir = os.path.dirname(log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            file_handler.addFilter(_ContextFilter())
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning(f"Failed to configure file logging at {log_path}: {e}")

    logger.propagate = False

    _LOGGING_CONFIGURED = True
    return logger


logger = setup_logging()
