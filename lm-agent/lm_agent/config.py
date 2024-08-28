import sys
import logging
from pathlib import Path
from typing import Optional

from pydantic import AnyHttpUrl, Field
from pydantic_core import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from lm_agent.constants import LogLevelEnum


DEFAULT_DOTENV_PATH = Path("/etc/default/license-manager-agent")
DEFAULT_CACHE_DIR = Path.home() / Path(".cache/license-manager")
DEFAULT_LOG_DIR = Path("/var/log/license-manager-agent")
DEFAULT_BIN_PATH = Path(__file__).parent.parent / "bin"


class Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM_AGENT_", e.g.
    LM_AGENT_LOG_LEVEL=DEBUG
    """

    # Deployment environment
    DEPLOY_ENV: str = "LOCAL"

    # Log level
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    # Base URL of the License Manager API
    BACKEND_BASE_URL: AnyHttpUrl = Field("http://127.0.0.1:8000")

    # Location of the log directory
    LOG_BASE_DIR: Optional[Path] = DEFAULT_LOG_DIR

    # Token cache directory
    CACHE_DIR: Path = DEFAULT_CACHE_DIR

    # Path to Slurm binaries
    SCONTROL_PATH: Path = Path("/usr/bin/scontrol")
    SACCTMGR_PATH: Path = Path("/usr/bin/sacctmgr")
    SQUEUE_PATH: Path = Path("/usr/bin/squeue")

    # Path to the binary for lmutil (needed for FlexLM licenses)
    LMUTIL_PATH: Path = DEFAULT_BIN_PATH / "lmutil"

    # Path to the binary for rlmutil (needed for RLM licenses)
    RLMUTIL_PATH: Path = DEFAULT_BIN_PATH / "rlmutil"

    # Path to the binary for lstc_qrun (needed for LS-Dyna licenses)
    LSDYNA_PATH: Path = DEFAULT_BIN_PATH / "lstc_qrun"

    # Path to the binary for lmxendutil (needed for LM-X licenses)
    LMXENDUTIL_PATH: Path = DEFAULT_BIN_PATH / "lmxendutil"

    # Path to the binary for olixtool (needed for OLicense licenses)
    OLIXTOOL_PATH: Path = DEFAULT_BIN_PATH / "olixtool"

    # Reservation name for reconciliation
    RESERVATION_IDENTIFIER: str = "license-manager-reservation"

    # License Manager user name to create reservations
    LM_USER: str = "license-manager"

    # Sentry specific settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_SAMPLE_RATE: Optional[float] = Field(1.0, gt=0.0, le=1.0)

    # OIDC config for machine-to-machine security
    OIDC_DOMAIN: str
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str
    OIDC_USE_HTTPS: bool = True

    # If set to `True`, reconcile will be triggered by Prolog/Epilog. Set to `False` to disable this.
    USE_RECONCILE_IN_PROLOG_EPILOG: bool = True

    # Stat interval used to report the cluster status to the API
    STAT_INTERVAL: int = 60

    # Timeout for the license server binaries
    TOOL_TIMEOUT: int = 6  # seconds

    # Encoding used for decoding the output of the license server binaries
    ENCODING: str = "utf-8"

    model_config = SettingsConfigDict(
        env_prefix="LM_AGENT_",
        env_file=DEFAULT_DOTENV_PATH if DEFAULT_DOTENV_PATH.is_file() else Path(".env"),
    )


def init_settings() -> Settings:
    """
    Build SETTINGS, and offer a way to gracefully fail if required settings cannot be loaded
    """
    try:
        # ignoring call-arg because we expect the parameters to
        # be set either by the environment or the dotenv file
        return Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        logger = logging.getLogger("lm_agent.config")
        logger.error(f"Failed to load settings: {str(e)}")
        sys.exit(1)


settings = init_settings()
