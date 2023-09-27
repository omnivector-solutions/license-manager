"""License Server schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class LicenseServerCreateSchema(BaseCreateSchema):
    """
    License server to be created in the database.
    """

    config_id: int = Field(
        ...,
        title="Configuration ID",
        description="The ID of the configuration that the license server belongs to.",
    )
    host: str = Field(..., title="Host", description="The host of the license server.")
    port: PositiveInt = Field(..., title="Port", description="The port of the license server.")


class LicenseServerWithoutConfigIdCreateSchema(BaseCreateSchema):
    """
    License server to be created by configurations endpoint.

    The config_id will be handled in the endpoint.
    """

    host: str = Field(..., title="Host", description="The host of the license server.")
    port: PositiveInt = Field(..., title="Port", description="The port of the license server.")


class LicenseServerWithOptionalIdUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    id: Optional[int] = Field(None, title="ID", description="The ID of the license server.")
    host: Optional[str] = Field(None, title="Host", description="The host of the license server.")
    port: Optional[PositiveInt] = Field(None, title="Port", description="The port of the license server.")


class LicenseServerUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    config_id: Optional[int] = Field(
        None,
        title="Configuration ID",
        description="The ID of the configuration that the license server belongs to.",
    )
    host: Optional[str] = Field(None, title="Host", description="The host of the license server.")
    port: Optional[PositiveInt] = Field(None, title="Port", description="The port of the license server.")


class LicenseServerSchema(BaseModel):
    """
    License server response from the database.
    """

    id: int = Field(..., title="ID", description="The ID of the license server.")
    config_id: int = Field(
        ...,
        title="Configuration ID",
        description="The ID of the configuration that the license server belongs to.",
    )
    host: str = Field(..., title="Host", description="The host of the license server.")
    port: PositiveInt = Field(..., title="Port", description="The port of the license server.")

    class Config:
        orm_mode = True
