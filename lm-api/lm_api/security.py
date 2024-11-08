"""
Instantiates armada-security resources for auth on api endpoints using project settings.
Also provides a factory function for TokenSecurity to reduce boilerplate.
"""

import typing

from typing_extensions import Self

from armasec import Armasec, TokenPayload
from armasec.token_security import PermissionMode
from fastapi import Depends
from loguru import logger
from pydantic import model_validator, EmailStr

from lm_api.config import settings


guard = Armasec(
    domain=settings.ARMASEC_DOMAIN,
    debug_logger=logger.debug if settings.ARMASEC_DEBUG else None,
    use_https=settings.ARMASEC_USE_HTTPS,
)


class IdentityPayload(TokenPayload):
    """
    Provide an extension of TokenPayload that includes the user's identity.
    """

    email: typing.Optional[EmailStr] = None
    organization: typing.Optional[typing.Union[str, typing.Dict]] = None
    organization_id: typing.Optional[str] = None

    @model_validator(mode="after")
    def extract_organization(self) -> Self:
        """
        Extracts the organization_id from the organization payload.

        The payload is expected to look like:
        {
            ...,
            "organization": {
                "adf99e01-5cd5-41ac-a1af-191381ad7780": {
                    ...
                }
            }
        }
        """
        if self.organization is None:
            return typing.cast(Self, self)
        elif len(self.organization) != 1 and isinstance(self.organization, dict):
            raise ValueError(
                f"Organization payload did not include exactly one value: {getattr(self, 'organization')}"
            )
        setattr(self, "organization_id", next(iter(self.organization)))
        return typing.cast(Self, self)


def lockdown_with_identity(*scopes: str, permission_mode: PermissionMode = PermissionMode.SOME):
    """
    Provide a wrapper to be used with dependency injection to extract identity on a secured route.
    """

    def dependency(
        token_payload: TokenPayload = Depends(guard.lockdown(*scopes, permission_mode=permission_mode)),
    ) -> IdentityPayload:
        """
        Provide an injectable function to lockdown a route and extract the identity payload.
        """
        return IdentityPayload.model_validate(token_payload, from_attributes=True)

    return dependency
