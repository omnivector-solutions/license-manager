"""
Configuration of the agent running in the cluster
"""

from enum import Enum
import typing

from pkg_resources import get_supported_platform, resource_filename
from pydantic import BaseSettings, DirectoryPath, Field, validator
from pydantic.main import BaseModel


class LogLevelEnum(str, Enum):
    """
    Log level name enforcement
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_JWT_REGEX = r"[a-zA-Z0-9+/]+\.[a-zA-Z0-9+/]+\.[a-zA-Z0-9+/]"
_URL_REGEX = r"http[s]?://.+"
_DEFAULT_BINDIR = resource_filename("licensemanager2.agent", get_supported_platform())


class LicenseService(BaseModel):
    """
    A license service such as "flexlm", with a set of host-port tuples
    representing the network location where the service is listening.
    """
    name: str
    hostports: typing.List[typing.Tuple[str, int]]


class LicenseServiceCollection(BaseModel):
    """
    A collection of LicenseServices, mapped by their names
    """
    services: typing.Dict[str, LicenseService]

    @classmethod
    def from_env_string(cls, services):
        """
        @returns LicenseServiceCollection from parsing colon-separated env input

        The syntax is:

        - servicename:host:port e.g. "flexlm:172.0.1.2:2345"

        - each entry separated by spaces e.g.
          "flexlm:172.0.1.2:2345 abclm:172.0.1.3:2319"

        - if the same service appears twice in the list they will be
          merged, e.g.:
          "flexlm:173.0.1.2:2345 flexlm:172.0.1.3:2345"
          -> (pseudodata) "flexlm": [("173.0.1.2", 2345), "173.0.1.3", 2345)]
        """
        self = cls(services={})
        services = services.split()
        for item in services:
            name, host, port = item.split(':', 2)

            svc = self.services.setdefault(name, LicenseService(name=name, hostports=[]))
            svc.hostports.append((host, int(port)))

        return self


class _Settings(BaseSettings):
    """
    App config.

    If you are setting these in the environment, you must prefix "LM2_AGENT_", e.g.
    LM2_AGENT_LOG_LEVEL=DEBUG
    """

    # base url of an endpoint serving the licensemanager2 backend
    # ... I tried using AnyHttpUrl but mypy complained
    BACKEND_BASE_URL: str = Field("http://127.1:8000", regex=_URL_REGEX)

    # a JWT API token for accessing the backend
    BACKEND_API_TOKEN: str = Field("test.api.token", regex=_JWT_REGEX)

    # a path to a folder containing binaries for license management tools
    BIN_PATH: DirectoryPath = _DEFAULT_BINDIR

    # list of separated service descriptions to check.
    # see LicenseServiceCollection.from_env_string for syntax
    SERVICE_ADDRS: str = "flexlm:127.0.0.1:2345"

    # interval, in seconds: how long between license count checks
    STAT_INTERVAL: int = 5 * 60

    # debug mode turns on certain dangerous operations
    DEBUG: bool = False

    # log level (everything except sql tracing)
    LOG_LEVEL: LogLevelEnum = LogLevelEnum.INFO

    class Config:
        env_prefix = "LM2_AGENT_"

    @validator("SERVICE_ADDRS")
    def validate_service_addrs(s):
        """
        Convert the string form into a LicenseServiceCollection
        """
        return LicenseServiceCollection.from_env_string(s)


SETTINGS = _Settings()
