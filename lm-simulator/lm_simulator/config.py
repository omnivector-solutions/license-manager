from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOST: str = "localhost"
    DATABASE_USER: str = "local-user"
    DATABASE_PSWD: str = "local-pswd"
    DATABASE_NAME: str = "local-db"
    DATABASE_PORT: int = 5432

    TEST_DATABASE_HOST: str = "localhost"
    TEST_DATABASE_USER: str = "test-db-user"
    TEST_DATABASE_PSWD: str = "test-db-pswd"
    TEST_DATABASE_NAME: str = "test-db-name"
    TEST_DATABASE_PORT: int = 5433

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
