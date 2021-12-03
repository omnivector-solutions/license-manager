"""
Custom exceptions for the License Manager Agent.
"""

from buzz import Buzz


class LicenseManagerBackendConnectionError(Buzz):
    """Exception for backend connection issues."""


class LicenseManagerBackendVersionError(Buzz):
    """Exception for backend/agent version mismatches."""


class LicenseManagerAuthTokenError(Buzz):
    """Exception for backend connection issues."""
