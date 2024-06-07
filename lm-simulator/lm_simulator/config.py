from pydantic import BaseSettings, Field

_DB_RX = r"^(sqlite|postgresql)://.+$"


class Settings(BaseSettings):
    DATABASE_URL: str = Field("sqlite:///./sqlite.db?check_same_thread=false", regex=_DB_RX)

    class Config:
        env_file = ".env"


settings = Settings()
