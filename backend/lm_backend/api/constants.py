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


class Permissions(str, Enum):
    """
    Describe the permissions that may be used for protecting LM Backend routes.
    """

    BOOKING_VIEW = "license-manager:booking:view"
    BOOKING_EDIT = "license-manager:booking:edit"
    CONFIG_VIEW = "license-manager:config:view"
    CONFIG_EDIT = "license-manager:config:edit"
    LICENSE_VIEW = "license-manager:license:view"
    LICENSE_EDIT = "license-manager:license:edit"


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"
