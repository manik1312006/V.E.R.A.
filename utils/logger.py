"""Logging utilities for V.E.R.A."""

import logging
import os
from rich.logging import RichHandler


def setup_logger(
    name: str = "vera",
    level: int = logging.INFO,
    log_to_file: bool = True,
    logs_dir: str = "logs",
) -> logging.Logger:
    """Set up and return a configured logger.

    Args:
        name: Logger name.
        level: Logging level (default: INFO).
        log_to_file: Whether to also log to a file.
        logs_dir: Directory for log files.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(message)s",
        datefmt="[%X]",
    )

    # Console handler with Rich
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(logs_dir, "vera.log"),
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "vera") -> logging.Logger:
    """Get an existing logger by name.

    Args:
        name: Logger name (default: 'vera').

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
