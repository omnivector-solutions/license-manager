class LicenseManagerBackendConnectionError(Exception):
    """Exception for backend connection issues."""


class LicenseManagerBackendVersionError(Exception):
    """Exception for backend/agent version mismatches."""


class LicenseManagerEmptyReportError(Exception):
    """Exception for empty report when no licenses added in backend."""


class LicenseManagerNonSupportedServerTypeError(Exception):
    """Exception for entry with non supported server type."""


class LicenseManagerBadServerOutput(Exception):
    """Exception for license server bad output."""
