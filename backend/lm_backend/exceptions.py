"""
Custom exceptions for the License Manager Backend.
"""
from buzz import Buzz


class LicenseManagerFeatureConfigurationIncorrect(Buzz):
    """Exception for feature configuration incorrectly formatted."""
