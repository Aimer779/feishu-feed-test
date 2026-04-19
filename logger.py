"""Structured logging based on loguru."""

import sys

from loguru import logger

__all__ = ["init_logging", "get_logger"]


def init_logging(level: str = "INFO", log_file: str | None = None) -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )
    if log_file:
        logger.add(
            log_file,
            level=level,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            ),
            rotation="1 day",
            retention="7 days",
            encoding="utf-8",
        )


def get_logger(name: str | None = None):
    if name:
        return logger.bind(logger_name=name)
    return logger
