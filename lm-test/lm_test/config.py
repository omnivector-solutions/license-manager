from pathlib import Path

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Configurations to run the integration test.
    """

    # APIs endpoint
    LM_API_BASE_URL: str
    LM_SIM_BASE_URL: str

    # License Manager Simulator repo path
    LM_SIM_PATH: Path

    # Cluster configurations
    CLUSTER_ID: str

    # OIDC config for machine-to-machine security
    OIDC_DOMAIN: str
    OIDC_CLIENT_ID: str
    OIDC_CLIENT_SECRET: str

    class Config:
        env_file = Path(".env")


settings = Settings()
