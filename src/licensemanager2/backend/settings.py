"""
Configuration of the application
"""
from enum import Enum
import re
from typing import Optional

from pydantic import BaseSettings, validator


class LogLevelEnum(str, Enum):
    """
    Log level name enforcement
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_DB_RX = re.compile(r"^(sqlite|postgresql)://.+$")


class _Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_", e.g.
    LM2_ASGI_ROOT_PATH=/staging
    """

    ASGI_ROOT_PATH: str = ""
    ALLOW_ORIGINS_REGEX: str = r"https://.*\.omnivector\.solutions"
    DATABASE_URL: str = "sqlite:///./sqlite.db"

    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO
    LOG_LEVEL_SQL: Optional[LogLevelEnum]

    class Config:
        env_prefix = "LM2_"

    @validator("DATABASE_URL")
    def database_url_pattern(cls, v):
        """
        DATABASE connection strings must match a specific pattern
        """
        if not _DB_RX.match(v):
            raise ValueError(
                f"LM2_DATABASE_URL must be sqlite:// or postgresql:// (was {v!r})"
            )
        return v


SETTINGS = _Settings()
