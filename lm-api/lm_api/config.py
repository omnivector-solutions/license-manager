from typing import Optional, Annotated

from pydantic import Field, confloat

from lm_api.constants import LogLevelEnum
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    App config.
    """

    DEPLOY_ENV: str = "LOCAL"

    # Sentry settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: Annotated[float, confloat(gt=0, le=1.0)] = 0.01
    SENTRY_SAMPLE_RATE: Annotated[float, confloat(gt=0.0, le=1.0)] = 0.25
    SENTRY_PROFILING_SAMPLE_RATE: Annotated[float, confloat(gt=0.0, le=1.0)] = 0.01

    # vv should be specified as something like /staging
    # to match where the API is deployed in API Gateway
    ASGI_ROOT_PATH: str = ""

    # Database settings
    DATABASE_HOST: str = "localhost"
    DATABASE_USER: str = "local-user"
    DATABASE_PSWD: str = "local-pswd"
    DATABASE_NAME: str = "local-db"
    DATABASE_PORT: int = 5432

    # Test database settings
    TEST_DATABASE_HOST: str = "localhost"
    TEST_DATABASE_USER: str = "test-db-user"
    TEST_DATABASE_PSWD: str = "test-db-pswd"
    TEST_DATABASE_NAME: str = "test-db-name"
    TEST_DATABASE_PORT: int = 5433

    # Enable multi-tenancy so that the database is determined by the client_id in the auth token
    MULTI_TENANCY_ENABLED: bool = Field(False)

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # log level (sql tracing)
    LOG_LEVEL_SQL: Optional[LogLevelEnum] = None

    # Security Settings. For details, see https://github.com/omnivector-solutions/armsec
    ARMASEC_DOMAIN: str
    ARMASEC_DEBUG: bool = Field(False)
    ARMASEC_ADMIN_DOMAIN: Optional[str] = None
    ARMASEC_ADMIN_MATCH_KEY: Optional[str] = None
    ARMASEC_ADMIN_MATCH_VALUE: Optional[str] = None
    ARMASEC_USE_HTTPS: bool = Field(True)
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
