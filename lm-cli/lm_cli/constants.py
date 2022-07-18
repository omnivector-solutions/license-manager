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
