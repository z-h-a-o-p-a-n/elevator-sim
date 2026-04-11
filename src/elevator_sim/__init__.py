"""elevator-sim: A simplified simulation of an intelligent elevator system."""

import logging
import os
import sys

__version__ = "0.1.0"

_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def configure_logging(level: str | None = None) -> None:
    """Configure the root logger.

    Priority: *level* argument > ``LOG_LEVEL`` environment variable > ``INFO``.
    """
    if level is None:
        level = os.environ.get("LOG_LEVEL", "INFO")
    level = level.upper()
    if level not in _LOG_LEVELS:
        raise ValueError(f"Invalid log level: {level!r}. Choose from {', '.join(sorted(_LOG_LEVELS))}.")
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(handler)
