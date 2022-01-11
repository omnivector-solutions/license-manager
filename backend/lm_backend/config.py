from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl


class LogLevelEnum(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DeployEnvEnum(str, Enum):
    """
    Describes the environment where the app is currently deployed.
    """

    PROD = "PROD"
    STAGING = "STAGING"
    LOCAL = "LOCAL"


class Settings(BaseSettings):
    """
    App config.
    """

    DEPLOY_ENV: Optional[DeployEnvEnum] = DeployEnvEnum.LOCAL

    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_SAMPLE_RATE: Optional[float] = Field(1.0, gt=0.0, le=1.0)

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
