"""
Instantiates armada-security resources for auth on api endpoints using project settings.
Also provides a factory function for TokenSecurity to reduce boilerplate.
"""

import typing

from armasec import Armasec, TokenPayload
from armasec.schemas import DomainConfig
from armasec.token_security import PermissionMode
from fastapi import Depends
from loguru import logger
from pydantic import EmailStr

from lm_backend.config import settings


def get_domain_configs() -> typing.List[DomainConfig]:
    domain_configs = [
        DomainConfig(
            domain=settings.ARMASEC_DOMAIN,
            audience=settings.ARMASEC_AUDIENCE,
            debug_logger=logger.debug if settings.ARMASEC_DEBUG else None,
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
                debug_logger=logger.debug if settings.ARMASEC_DEBUG else None,
            )
        )
    return domain_configs


guard = Armasec(domain_configs=get_domain_configs())


class IdentityPayload(TokenPayload):
    """
    Provide an extension of TokenPayload that includes the user's identity.
    """

    email: typing.Optional[EmailStr] = None


def lockdown_with_identity(*scopes: str, permission_mode: PermissionMode = PermissionMode.ALL):
    """
    Provide a wrapper to be used with dependency injection to extract identity on a secured route.
    """

    def dependency(
        token_payload: TokenPayload = Depends(guard.lockdown(*scopes, permission_mode=permission_mode))
    ) -> IdentityPayload:
        """
        Provide an injectable function to lockdown a route and extract the identity payload.
        """
        return IdentityPayload.parse_obj(token_payload)

    return dependency
