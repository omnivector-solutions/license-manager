"""
Instantiates armada-security resources for auth on api endpoints using project settings.
Also provides a factory function for TokenSecurity to reduce boilerplate.
"""

import logging
from typing import List

from armasec import Armasec
from armasec.schemas import DomainConfig

from lm_backend.config import settings


def get_domain_configs() -> List[DomainConfig]:
    domain_configs = [
        DomainConfig(
            domain=settings.ARMASEC_DOMAIN,
            audience=settings.ARMASEC_AUDIENCE,
            debug_logger=logging.getLogger("armasec").debug if settings.ARMASEC_DEBUG else None,
        )
    ]
    if all(
        [
            settings.ARMASEC_ADMIN_DOMAIN,
            settings.ARMASEC_ADMIN_AUDIENCE,
            settings.ARMASEC_ADMIN_MATCH_KEY,
            settings.ARMASEC_ADMIN_MATCH_VALUE,
        ]
    ):
        domain_configs.append(
            DomainConfig(
                domain=settings.ARMASEC_ADMIN_DOMAIN,
                audience=settings.ARMASEC_ADMIN_AUDIENCE,
                match_keys={settings.ARMASEC_ADMIN_MATCH_KEY: settings.ARMASEC_ADMIN_MATCH_VALUE},
                debug_logger=logging.getLogger("armasec").debug if settings.ARMASEC_DEBUG else None,
            )
        )
    return domain_configs


guard = Armasec(domain_configs=get_domain_configs())
