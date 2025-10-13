"""Logging configuration using loguru."""

import sys
from loguru import logger
from src.config import get_settings

settings = get_settings()


def setup_logger() -> None:
    """Configure loguru logger with file and console handlers."""
    # Remove default handler
    logger.remove()

    # Console handler with color
    logger.add(
        sys.stdout,
        format=settings.log_format_console,
        level=settings.log_level,
        colorize=True,
    )

    # File handler with rotation
    logger.add(
        settings.log_file,
        format=settings.log_format_file,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
    )

    logger.info("Logger initialized")


# Initialize logger on import
setup_logger()
