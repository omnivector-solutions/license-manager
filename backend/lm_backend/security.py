"""
Instantiates armada-security resources for auth on api endpoints using project settings.
Also provides a factory function for TokenSecurity to reduce boilerplate.
"""

import logging

from armasec import Armasec

from lm_backend.config import settings

guard = Armasec(
    settings.ARMASEC_DOMAIN,
    audience=settings.ARMASEC_AUDIENCE,
    debug_logger=logging.getLogger("armasec").debug if settings.ARMASEC_DEBUG else None,
)
