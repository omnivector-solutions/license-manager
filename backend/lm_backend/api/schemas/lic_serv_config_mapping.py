"""Schema for license server config mapping."""
from pydantic import BaseModel


class LicServConfigMappingCreateSchema(BaseModel):
    """
    Represents the many-to-many relationship between license servers and configs.
    """

    license_server_id: int
    config_id: int


class LicServConfigMappingUpdateSchema(BaseModel):
    """
    Represents the many-to-many relationship between license servers and configs.
    """

    license_server_id: int
    config_id: int


class LicServConfigMapping(BaseModel):
    """
    Represents the many-to-many relationship between license servers and configs.
    """

    license_server_id: int
    config_id: int

    class Config:
        orm_mode = True
