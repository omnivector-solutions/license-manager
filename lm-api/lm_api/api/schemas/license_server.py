"""License Server schemas for the License Manager API."""
import re
from typing import Optional

from pydantic import field_validator, ConfigDict, BaseModel, Field, PositiveInt

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


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

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        HOST = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"  # noqa: W605
        if not re.match(HOST, value):
            raise ValueError("Host must match the regex [a-z0-9-.]+")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        if value > 65535:
            raise ValueError("Port must be less than or equal to 65535")
        return value


class LicenseServerWithoutConfigIdCreateSchema(BaseCreateSchema):
    """
    License server to be created by configurations endpoint.

    The config_id will be handled in the endpoint.
    """

    host: str = Field(..., title="Host", description="The host of the license server.")
    port: PositiveInt = Field(..., title="Port", description="The port of the license server.")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        HOST = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"  # noqa: W605
        if not re.match(HOST, value):
            raise ValueError("Host must match the regex [a-z0-9-.]+")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        if value > 65535:
            raise ValueError("Port must be less than or equal to 65535")
        return value


class LicenseServerWithOptionalIdUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    id: Optional[int] = Field(None, title="ID", description="The ID of the license server.")
    host: Optional[str] = Field(None, title="Host", description="The host of the license server.")
    port: Optional[PositiveInt] = Field(None, title="Port", description="The port of the license server.")

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        HOST = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"  # noqa: W605
        if not re.match(HOST, value):
            raise ValueError("Host must match the regex [a-z0-9-.]+")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        if value > 65535:
            raise ValueError("Port must be less than or equal to 65535")
        return value


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

    @field_validator("host")
    @classmethod
    def validate_host(cls, value):
        HOST = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"  # noqa: W605
        if not re.match(HOST, value):
            raise ValueError("Host must match the regex [a-z0-9-.]+")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value):
        if value > 65535:
            raise ValueError("Port must be less than or equal to 65535")
        return value


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
    model_config = ConfigDict(from_attributes=True)
