from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl


class LogLevelEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    App config.
    """

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False
    SENTRY_DSN: Optional[str] = None

    # vv should be specified as something like /staging
    # to match where the API is deployed in API Gateway
    ASGI_ROOT_PATH: str = ""

    # database to connect
    DATABASE_URL: str

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # log level (sql tracing)
    LOG_LEVEL_SQL: Optional[LogLevelEnum]

    # Security Settings. For details, see https://github.com/omnivector-solutions/armsec
    ARMASEC_DOMAIN: str
    ARMASEC_AUDIENCE: Optional[HttpUrl]
    ARMASEC_DEBUG: bool = Field(False)

    class Config:
        env_file = ".env"


settings = Settings()
