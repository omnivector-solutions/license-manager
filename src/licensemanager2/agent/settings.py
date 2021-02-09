"""
Configuration of the agent running in the cluster
"""

from enum import Enum

from pydantic import BaseSettings


class LogLevelEnum(str, Enum):
    """
    Log level name enforcement
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class _Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_AGENT_", e.g.
    LM2_AGENT_LOG_LEVEL=DEBUG
    """

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    class Config:
        env_prefix = "LM2_AGENT_"


SETTINGS = _Settings()
