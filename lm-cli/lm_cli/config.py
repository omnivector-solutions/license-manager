"""
Configuration file, sets all the necessary environment variables.
Can load configuration from a dotenv file if supplied.
"""

from pathlib import Path
from sys import exit
from typing import Optional

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from lm_cli.render import terminal_message
from lm_cli.text_tools import conjoin


DEFAULT_DOTENV_PATH = Path("/etc/default/lm-cli")
OV_CONTACT = "Omnivector Solutions <info@omnivector.solutions>"


class Settings(BaseSettings):
    """
    Provide a ``pydantic`` settings model to hold configuration values loaded from the environment.
    """

    LM_CACHE_DIR: Path = Field(Path.home() / ".local/share/license-manager")
    LM_API_ENDPOINT: str = "http://localhost:8000/lm"

    # enable http tracing
    LM_DEBUG: bool = Field(False)

    # Computed values. Listed as Optional, but will *always* be set (or overridden) based on other values
    LM_LOG_PATH: Optional[Path] = None
    LM_USER_TOKEN_DIR: Optional[Path] = None
    LM_API_ACCESS_TOKEN_PATH: Optional[Path] = None
    LM_API_REFRESH_TOKEN_PATH: Optional[Path] = None

    # OIDC config for machine-to-machine security
    OIDC_DOMAIN: str
    OIDC_LOGIN_DOMAIN: Optional[str] = None
    OIDC_CLIENT_ID: str
    OIDC_MAX_POLL_TIME: int = 5 * 60  # 5 Minutes

    @model_validator(mode="after")
    def compute_extra_settings(self):
        """
        Compute settings values that are based on other settings values.
        """
        cache_dir = self.LM_CACHE_DIR
        cache_dir.mkdir(exist_ok=True, parents=True)

        log_dir = cache_dir / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        self.LM_LOG_PATH = log_dir / "lm-cli.log"

        token_dir = cache_dir / "token"
        token_dir.mkdir(exist_ok=True, parents=True)
        self.LM_USER_TOKEN_DIR = token_dir
        self.LM_API_ACCESS_TOKEN_PATH = token_dir / "access.token"
        self.LM_API_REFRESH_TOKEN_PATH = token_dir / "refresh.token"

        self.OIDC_LOGIN_DOMAIN = self.OIDC_LOGIN_DOMAIN or self.OIDC_DOMAIN

        return self

    model_config = SettingsConfigDict(
        env_file=DEFAULT_DOTENV_PATH if DEFAULT_DOTENV_PATH.is_file() else Path(".env")
    )


def build_settings(*args, **kwargs):
    """
    Return a Setting object and handle ValidationError with a message to the user.
    """
    try:
        return Settings(*args, **kwargs)
    except ValidationError:
        terminal_message(
            conjoin(
                "A configuration error was detected.",
                "",
                f"[yellow]Please contact [bold]{OV_CONTACT}[/bold] for support and trouble-shooting[/yellow]",
            ),
            subject="Configuration Error.",
        )
        exit(1)


settings = build_settings()
