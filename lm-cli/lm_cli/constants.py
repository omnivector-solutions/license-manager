"""
Constants that may be used throughout the CLI modules.
"""

from enum import Enum


class SortOrder(str, Enum):
    """
    Enum describing the type of sort orders that are available for list commands.
    """

    ASCENDING = "ascending"
    DESCENDING = "descending"
    UNSORTED = "unsorted"


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"
