"""
Enhanced logging configuration with structured JSON output.
Extracted from the main __init__.py for better modularity.
"""
import json
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """Configures structured JSON logging."""
    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)
    log_file = os.path.join(log_directory, "arxiv_mcp_server.log")

    # Custom JSON Formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": record.getMessage(),
                "logger_name": record.name,
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
            }
            if hasattr(record, "extra_data"):
                log_record.update(record.extra_data)
            return json.dumps(log_record)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplication
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a rotating file handler
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # Create a console handler for local development (optional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    return logging.getLogger(__name__)
