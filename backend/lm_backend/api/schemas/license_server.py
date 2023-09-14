"""License Server schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel, PositiveInt

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class LicenseServerCreateSchema(BaseCreateSchema):
    """
    License server to be created in the database.
    """

    config_id: int
    host: str
    port: PositiveInt


class LicenseServerWithoutConfigIdCreateSchema(BaseCreateSchema):
    """
    License server to be created by configurations endpoint.

    The config_id will be handled in the endpoint.
    """

    host: str
    port: PositiveInt


class LicenseServerWithOptionalIdUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    id: Optional[int] = None
    host: Optional[str] = None
    port: Optional[PositiveInt] = None


class LicenseServerUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    config_id: Optional[int] = None
    host: Optional[str] = None
    port: Optional[PositiveInt] = None


class LicenseServerSchema(BaseModel):
    """
    License server response from the database.
    """

    id: int
    config_id: int
    host: str
    port: PositiveInt

    class Config:
        orm_mode = True
