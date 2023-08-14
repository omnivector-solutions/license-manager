from buzz import Buzz


class AuthTokenError(Buzz):
    """Exception for OIDC connection issues."""

class BadResponse(Buzz):
    """Exception for backend connection issues."""
