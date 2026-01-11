"""Logging setup."""

import logging
from logging.handlers import RotatingFileHandler

from trade_hub.infra.settings import settings


def setup_logging():
    """Configure application logging with file rotation."""
    log_dir = settings.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / settings.get("log_file")
    log_level = getattr(logging, settings.get("log_level", "INFO"))
    max_bytes = settings.get("log_max_size_mb", 10) * 1024 * 1024
    backup_count = settings.get("log_backup_count", 5)

    # Log format: string format for readability
    log_format = "%(levelname)s %(asctime)s %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S"
    formatter = logging.Formatter(log_format, datefmt=date_format)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.ERROR)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    app_logger = logging.getLogger("trade_hub")
    app_logger.setLevel(log_level)

    return app_logger


def get_logger(name: str = "trade_hub") -> logging.Logger:
    """Get logger by name."""
    return logging.getLogger(name)
