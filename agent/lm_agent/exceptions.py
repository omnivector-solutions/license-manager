"""
Custom exceptions for the License Manager Agent.
"""

from buzz import Buzz


class LicenseManagerAuthTokenError(Buzz):
    """Exception for backend connection issues."""


class LicenseManagerBackendConnectionError(Buzz):
    """Exception for backend connection issues."""


class LicenseManagerBackendVersionError(Buzz):
    """Exception for backend/agent version mismatches."""


class LicenseManagerEmptyReportError(Buzz):
    """Exception for empty report when no licenses added in backend."""


class LicenseManagerNonSupportedServerTypeError(Buzz):
    """Exception for entry with non supported server type."""


class LicenseManagerBadServerOutput(Buzz):
    """Exception for license server bad output."""
