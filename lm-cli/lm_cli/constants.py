"""
Provide constants that may be used throughout the CLI modules.
"""

from enum import Enum


class SortOrder(str, Enum):
    """
    Enum descring the type of sort orders that are available for list commands.
    """

    ASCENDING = "ascending"
    DESCENDING = "descending"
    UNSORTED = "unsorted"
