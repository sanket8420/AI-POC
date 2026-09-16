"""
Central logging setup.

Every layer of the platform (connectors, pipeline, document intelligence)
writes to the SAME logger so that a single ingestion run produces one
coherent trail in logs/ingestion.log — useful for debugging and for
demonstrating traceability to stakeholders.
"""

import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "ingestion.log")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger. Safe to call repeatedly (e.g. once per
    module) — handlers are only attached once per logger name.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
