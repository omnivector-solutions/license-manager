"""Schemas for license servers."""
from enum import Enum

from pydantic import BaseModel, validator


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"


class LicenseServerCreateSchema(BaseModel):
    """
    License server to be created in the database.
    """

    host: str
    port: int
    type: LicenseServerType

    @validator("port")
    def port_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Port must be positive")
        return v


class LicenseServerUpdateSchema(BaseModel):
    """
    License server to be updated in the database.
    """

    host: str = None
    port: str = None
    type: LicenseServerType = None

    @validator("port")
    def port_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Port must be positive")
        return v


class LicenseServerSchema(BaseModel):
    """
    License server response from the database.
    """

    id: int
    host: str
    port: int
    type: LicenseServerType

    class Config:
        orm_mode = True
