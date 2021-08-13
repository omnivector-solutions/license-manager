import bz2
import logging
import os
from logging.handlers import RotatingFileHandler

from lm_agent.config import settings

DEFAULT_FORMAT = "[%(asctime)s;%(levelname)s] %(filename)s:%(lineno)s - " "%(funcName)20s %(message)s"

level = getattr(logging, settings.LOG_LEVEL)
logger = logging.getLogger("license-manager-agent-logger")
logger.setLevel(level)


def _rotator(source: str, dest: str):
    """Rotate log and compress with bz2."""
    with open(source, "rb") as source_file:
        with bz2.open(dest, "wb") as bz2_file:
            bz2_file.write(source_file.read())
    os.remove(source)


def _namer(name: str):
    """Rename for the rotated log file."""
    return f"{name}.bz2"


def _formatter():
    """logging.Formatter configured the way we like it to look."""
    ret = logging.Formatter(DEFAULT_FORMAT)
    return ret


def init_logging(command_type: str):
    """Create and return the logging handler."""
    if settings.LOG_BASE_DIR is not None:
        _rotating_file_handler(f"{settings.LOG_BASE_DIR}/{command_type}.log")
    else:
        _default_logging()


def _rotating_file_handler(log_file: str):
    """Configure the rotating file handler."""
    global logger

    # Rotate the log file at 5MB, keep 10 rotations.
    handler = RotatingFileHandler(
        log_file,
        backupCount=10,
        maxBytes=5242880,
    )
    handler.rotator = _rotator
    handler.namer = _namer

    level = getattr(logging, settings.LOG_LEVEL)
    handler.setLevel(level)
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

    level = getattr(logging, settings.LOG_LEVEL)
    handler.setLevel(level)
    logger.addHandler(handler)


log = logger
