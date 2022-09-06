"""
Configuration file, sets all the necessary environment variables.
Can load configuration from a dotenv file if supplied.
"""

from pathlib import Path
from sys import exit
from typing import Optional

from pydantic import AnyHttpUrl, BaseSettings, Field, ValidationError, root_validator

from lm_cli.render import terminal_message
from lm_cli.text_tools import conjoin


DEFAULT_DOTENV_PATH = Path("/etc/default/lm-cli")
OV_CONTACT = "Omnivector Solutions <info@omnivector.solutions>"


class Settings(BaseSettings):
    """
    Provide a ``pydantic`` settings model to hold configuration values loaded from the environment.
    """

    LM_CACHE_DIR: Path = Field(Path.home() / ".local/share/license-manager")
    LM_API_ENDPOINT: AnyHttpUrl = Field("https://armada-k8s.staging.omnivector.solutions/lm/api/v1")

    # enable http tracing
    LM_DEBUG: bool = Field(False)

    # Computed values. Listed as Optional, but will *always* be set (or overridden) based on other values
    LM_LOG_PATH: Optional[Path]
    LM_USER_TOKEN_DIR: Optional[Path]
    LM_API_ACCESS_TOKEN_PATH: Optional[Path]
    LM_API_REFRESH_TOKEN_PATH: Optional[Path]

    # OIDC config for machine-to-machine security
    OIDC_DOMAIN: str
    OIDC_LOGIN_DOMAIN: Optional[str]
    OIDC_AUDIENCE: str
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str
    OIDC_MAX_POLL_TIME: int = 5 * 60  # 5 Minutes

    IDENTITY_CLAIMS_KEY: str = "email"

    @root_validator(skip_on_failure=True)
    def compute_extra_settings(cls, values):
        """
        Compute settings values that are based on other settings values.
        """
        cache_dir = values["LM_CACHE_DIR"]
        cache_dir.mkdir(exist_ok=True, parents=True)

        log_dir = cache_dir / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        values["LM_LOG_PATH"] = log_dir / "lm-cli.log"

        token_dir = cache_dir / "token"
        token_dir.mkdir(exist_ok=True, parents=True)
        values["LM_USER_TOKEN_DIR"] = token_dir
        values["LM_API_ACCESS_TOKEN_PATH"] = token_dir / "access.token"
        values["LM_API_REFRESH_TOKEN_PATH"] = token_dir / "refresh.token"

        values.setdefault("OIDC_LOGIN_DOMAIN", values["OIDC_DOMAIN"])

        return values

    class Config:
        if DEFAULT_DOTENV_PATH.is_file():
            env_file = DEFAULT_DOTENV_PATH
        else:
            env_file = Path(".env")


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
