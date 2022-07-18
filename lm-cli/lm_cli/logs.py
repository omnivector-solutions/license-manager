"""
Initializers for logging.
"""

import sys

from loguru import logger

from lm_cli.config import settings


def init_logs(verbose=False):
    """
    Initialize logging.

    If LM_LOG_PATH is set in the config, add a rotatating file log handler.
    Logs will be retained for 1 week.

    If verbose is supplied, add a stdout handler at the DEBUG level.
    """
    # Remove default stderr handler at level INFO
    logger.remove()

    if verbose:
        logger.add(sys.stdout, level="DEBUG")

    if settings.LM_LOG_PATH is not None:
        logger.add(settings.LM_LOG_PATH, rotation="00:00", retention="1 week", level="DEBUG")
    logger.debug("Logging initialized")
