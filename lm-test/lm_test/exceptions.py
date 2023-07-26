"""
Custom exceptions.
"""
from buzz import Buzz


class AuthTokenError(Buzz):
    """Exception for token acquisition error."""


class ResponseNotJSONError(Buzz):
    """Exception for response payload error."""


class ResponseError(Buzz):
    """Exception for wrong status code in the response."""


class JobFailedError(Buzz):
    """Exception for job failure."""
