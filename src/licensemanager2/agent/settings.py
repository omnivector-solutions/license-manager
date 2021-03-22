"""
Configuration of the agent running in the cluster
"""

from enum import Enum
from pkg_resources import get_supported_platform, resource_filename

from pydantic import BaseSettings, DirectoryPath, Field


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
_DEFAULT_BINDIR = resource_filename("licensemanager2.agent", get_supported_platform())


class _Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_AGENT_", e.g.
    LM2_AGENT_LOG_LEVEL=DEBUG
    """

    # base url of an endpoint serving the licensemanager2 backend
    # ... I tried using AnyHttpUrl but mypy complained
    BACKEND_BASE_URL: str = Field("http://127.1:8000", regex=_URL_REGEX)

    # a JWT API token for accessing the backend
    BACKEND_API_TOKEN: str = Field("test.api.token", regex=_JWT_REGEX)

    # a path to a folder containing binaries for license management tools
    BIN_PATH: DirectoryPath = _DEFAULT_BINDIR

    # interval, in seconds: how long between license count checks
    STAT_INTERVAL: int = 5*60

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    class Config:
        env_prefix = "LM2_AGENT_"


SETTINGS = _Settings()
