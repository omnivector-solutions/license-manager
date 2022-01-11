from enum import Enum
from typing import Optional

from pydantic import BaseSettings, Field


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

    If you are setting these in the environment, you must prefix "LM2_", e.g.
    LM2_ASGI_ROOT_PATH=/staging
    """

    DEPLOY_ENV: Optional[DeployEnvEnum] = DeployEnvEnum.LOCAL

    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_SAMPLE_RATE: Optional[float] = Field(1.0, gt=0.0, le=1.0)

    # vv should be specified as something like /staging
    # to match where the API is deployed in API Gateway
    ASGI_ROOT_PATH: str = ""

    # CORS origins filter
    ALLOW_ORIGINS_REGEX: str = r"https://.*\.omnivector\.solutions"

    # database to connect
    DATABASE_URL: str

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # log level (sql tracing)
    LOG_LEVEL_SQL: Optional[LogLevelEnum]

    class Config:
        env_prefix = "LM2_"
        env_file = ".env"


settings = Settings()
