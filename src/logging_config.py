"""Application logging configuration shared by the CLI and API."""

import logging
import os


def configure_logging() -> None:
    """Configure application logs once, without changing existing handlers."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
