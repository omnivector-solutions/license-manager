import logging
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, DirectoryPath, Field
from pydantic.error_wrappers import ValidationError

logger = logging.getLogger("lm_agent.config")


PRODUCT_FEATURE_RX = r"^.+?\..+$"
ENCODING = "UTF8"
TOOL_TIMEOUT = 6  # seconds


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
_ADDR_REGEX = r"\S+?:\S+?:\d+"
_DEFAULT_BIN_PATH = Path(__file__).parent.parent / "bin"


class Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_AGENT_", e.g.
    LM2_AGENT_LOG_LEVEL=DEBUG
    """

    # base url of an endpoint serving the licensemanager2 backend
    # ... I tried using AnyHttpUrl but mypy complained
    BACKEND_BASE_URL: str = Field("http://127.0.0.1:8000", regex=_URL_REGEX)

    # agent base url
    AGENT_BASE_URL: str = Field("http://127.0.0.1:8010", regex=_URL_REGEX)

    # location of the log directory
    LOG_BASE_DIR: Optional[str]

    # a JWT API token for accessing the backend
    BACKEND_API_TOKEN: str = Field("test.api.token", regex=_JWT_REGEX)

    # path to the license server features config file
    LICENSE_SERVER_FEATURES_CONFIG_PATH: Optional[str]

    # a path to a folder containing binaries for license management tools
    BIN_PATH: DirectoryPath = _DEFAULT_BIN_PATH

    # interval, in seconds: how long between license count checks
    STAT_INTERVAL: int = 5 * 60

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False

    # log level
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    class Config:
        env_file = "/etc/default/license-manager-agent"
        env_prefix = "LM2_AGENT_"


def init_settings() -> Settings:
    """
    Build SETTINGS, and offer a way to gracefully fail if required settings cannot be loaded

    TODO: Determine if this is true. If Settings is missing a required field, it should throw
          an exception that causes the uvicorn process to exit gracefully (with an error code)
    """
    try:
        return Settings()
    except ValidationError as e:
        logger.error(f"Failed to load settings: {str(e)}")
        # neither fastapi nor uvicorn appear to offer a way to do a graceful
        # shutdown as of now, so this is what we've got.
        sys.exit(1)


settings = init_settings()
