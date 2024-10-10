from enum import Enum


class LogLevelEnum(str, Enum):
    """
    Describe the available logging levels.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"
    DSLS = "dsls"
