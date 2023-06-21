from typing import Optional

from pydantic import BaseSettings, Field, HttpUrl

from lm_backend.constants import LogLevelEnum


class Settings(BaseSettings):
    """
    App config.
    """

    DEPLOY_ENV: str = "LOCAL"

    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_SAMPLE_RATE: float = Field(1.0, gt=0.0, le=1.0)

    # vv should be specified as something like /staging
    # to match where the API is deployed in API Gateway
    ASGI_ROOT_PATH: str = ""

    # database to connect
    DATABASE_URL: str

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # log level (sql tracing)
    LOG_LEVEL_SQL: Optional[LogLevelEnum] = None

    # Security Settings. For details, see https://github.com/omnivector-solutions/armsec
    ARMASEC_DOMAIN: str
    ARMASEC_AUDIENCE: Optional[HttpUrl] = None
    ARMASEC_DEBUG: bool = Field(False)
    ARMASEC_ADMIN_DOMAIN: Optional[str] = None
    ARMASEC_ADMIN_AUDIENCE: Optional[HttpUrl] = None
    ARMASEC_ADMIN_MATCH_KEY: Optional[str] = None
    ARMASEC_ADMIN_MATCH_VALUE: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
