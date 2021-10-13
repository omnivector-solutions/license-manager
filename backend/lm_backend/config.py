from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field


class LogLevelEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_", e.g.
    LM2_ASGI_ROOT_PATH=/staging
    """

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False
    SENTRY_DSN: Optional[str] = None

    # vv should be specified as something like /staging
    # to match where the API is deployed in API Gateway
    ASGI_ROOT_PATH: str = ""

    # CORS origins filter
    ALLOW_ORIGINS_REGEX: str = r"https://.*\.omnivector\.solutions"

    # database to connect
    DATABASE_URL: str = Field(
        "sqlite:///./sqlite.db?check_same_thread=true", regex=r"^(sqlite|postgresql|postgres)://.+$"
    )

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # log level (sql tracing)
    LOG_LEVEL_SQL: Optional[LogLevelEnum]

    class Config:
        env_prefix = "LM2_"
        env_file = ".env"


settings = Settings()
