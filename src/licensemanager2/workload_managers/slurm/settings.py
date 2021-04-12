"""
Configuration for slurmctld prolog and epilog
"""

from enum import Enum
from pathlib import Path
import sys

from pydantic import BaseSettings, DirectoryPath, Field, FilePath
from pydantic.error_wrappers import ValidationError


class LogLevelEnum(str, Enum):
    """
    Log level name enforcement
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_JWT_REGEX = r"[a-zA-Z0-9+/]+\.[a-zA-Z0-9+/]+\.[a-zA-Z0-9+/]"
_URL_REGEX = r"http[s]?://.+"
_SCONTROL_PATH = Path("/snap/bin/scontrol")
_COMMAND_LOG_BASE_PATH = Path("/srv/work")


class _Settings(BaseSettings):
    """
    Slurmctldprolog and Slurmctld Epilog config.
    If you are setting these in the environment, you must prefix
    "LM2_SLURM_CMD_", e.g. LM2_SLURM_CMD_LOG_LEVEL=DEBUG
    """

    # base url for the lm2 agent endpoint
    AGENT_BASE_URL: str = Field("http://127.1:8010", regex=_URL_REGEX)

    # a JWT API token for accessing the agent
    AGENT_JWT_TOKEN: str = Field("test.api.token", regex=_JWT_REGEX)

    # a path to a folder containing binaries for license management tools
    SCONTROL_PATH: FilePath = _SCONTROL_PATH

    # Command log path
    COMMAND_LOG_BASE_PATH: DirectoryPath = _COMMAND_LOG_BASE_PATH

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False

    # log level
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    class Config:
        env_prefix = "LM2_SLURM_CMD_"


def init_settings() -> _Settings:
    """
    Build SETTINGS, and offer a way to gracefully fail from environment errors
    """
    try:
        return _Settings()
    except ValidationError as e:
        print(e)
        sys.exit(1)


SETTINGS = init_settings()
