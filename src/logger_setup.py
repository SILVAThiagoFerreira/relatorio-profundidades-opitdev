"""Logging configuration for the report run."""

from __future__ import annotations

import logging
import sys

from .exceptions import ConfigError
from .models import AppConfig, ExecutionContext


def setup_logging(config: AppConfig, context: ExecutionContext) -> logging.Logger:
    """Configure file and console logging for a single run."""

    context.log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("depth_report")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    level = getattr(logging, config.logging_level.upper(), None)
    if not isinstance(level, int):
        raise ConfigError(f"Invalid logging level: {config.logging_level}")

    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    if config.file_logging:
        file_handler = logging.FileHandler(context.log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if config.console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("Run id: %s", context.run_id)
    logger.info("Output PDF: %s", context.output_pdf)
    logger.info("Output CSV: %s", context.output_csv)
    return logger
