#!/usr/bin/env python3
"""license_manager logging module."""
import bz2
import logging
import os

from logging.handlers import RotatingFileHandler


DEFAULT_FORMAT = (
    "[%(asctime)s;%(levelname)s] %(filename)s:%(lineno)s - "
    "%(funcName)20s %(message)s"
)

logger = logging.getLogger("license-manager")
logger.setLevel(logging.DEBUG)


def _rotator(source, dest):
    """Rotate log and compress with bz2."""
    with open(source, 'rb') as source_file:
        with bz2.open(dest, "wb") as bz2_file:
            bz2_file.write(source_file.read())
    os.remove(source)


def _namer(name):
    """Rename for the rotated log file."""
    return f"{name}.bz2"


def _formatter():
    """logging.Formatter configured the way we like it to look."""
    ret = logging.Formatter(DEFAULT_FORMAT)
    return ret


def init_logging(log_file=None):
    """Create and return the logging handler."""
    if not log_file:
        _default_logging()
    else:
        _rotating_file_handler(log_file)


def _rotating_file_handler(log_file):
    """Configure the rotating file handler."""
    global logger

    handler = RotatingFileHandler(
        log_file,
        backupCount=5,
        maxBytes=100000,
    )
    handler.rotator = _rotator
    handler.namer = _namer

    handler.setLevel(logging.DEBUG)
    handler.setFormatter(_formatter())
    logger.addHandler(handler)


def _default_logging():
    """Create a default log handler.

    Create a default log handler so we can execute code that uses the logger
    outside of or before the logger is initialized in the entrypoint.
    """
    global logger

    handler = logging.StreamHandler()
    handler.setFormatter(_formatter())
    logger.addHandler(handler)


log = logger
