from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DB_RX = r"^(sqlite|postgresql)://.+$"


class Settings(BaseSettings):
    DATABASE_URL: str = Field("sqlite:///./sqlite.db?check_same_thread=false", pattern=_DB_RX)

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
