"""
Custom exceptions for the License Manager Agent.
"""

from buzz import Buzz


class LicenseManagerAuthTokenError(Buzz):
    """Exception for backend connection issues."""


class LicenseManagerBackendConnectionError(Buzz):
    """Exception for backend connection issues."""


class LicenseManagerParseError(Buzz):
    """Exception for error during parsing of backend data."""


class LicenseManagerBackendVersionError(Buzz):
    """Exception for backend/agent version mismatches."""


class LicenseManagerEmptyReportError(Buzz):
    """Exception for empty report when no licenses added in backend."""


class LicenseManagerNonSupportedServerTypeError(Buzz):
    """Exception for entry with non supported server type."""


class LicenseManagerBadServerOutput(Buzz):
    """Exception for license server bad output."""


class CommandFailedToExecute(Buzz):
    """Exception for failed execution of command."""


class LicenseManagerFeatureConfigurationIncorrect(Buzz):
    """Exception for feature configuration incorrectly formatted."""


class LicenseManagerReservationFailure(Buzz):
    """Exception for failure during reservation management."""


class SqueueParserUnexpectedInputError(Buzz):
    """Unexpected squeue output."""


class ScontrolRetrievalFailure(Buzz):
    """Could not get SLURM data for job id."""
