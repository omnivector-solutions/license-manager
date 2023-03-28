"""
API request and response schemas.
"""
from pydantic import BaseModel, validator
from enum import Enum
from typing import Any, Optional


class BaseCreateSchema(BaseModel):
    """
    Base class for creating objects in the database.
    """
    def dict(self, *args, **kwargs) -> dict:
        """
        Convert the Pydantic model to a dictionary, but only include fields
        that are not None.
        """
        return super().dict(
            *args,
            exclude_unset=True,
            **kwargs
        )

class BaseUpdateSchema(BaseModel):
    """
    Base class for updating objects in the database.
    """
    id: Optional[int] = None

    def dict(self, *args, **kwargs) -> dict:
        """
        Convert the Pydantic model to a dictionary, but only include fields
        that are not None and not equal to the default value.
        """
        return super().dict(
            *args,
            exclude_unset=True,
            exclude={"id"},
            **kwargs
        )

    def update(self, obj: Any) -> Any:
        """
        Update the fields of an existing object using the fields in the
        Pydantic model.
        """
        update_data = self.dict(exclude_none=True, exclude={"id"})
        for field in update_data:
            setattr(obj, field, update_data[field])
        return obj


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"


class LicenseServerCreateSchema(BaseCreateSchema):
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


class LicenseServerUpdateSchema(BaseUpdateSchema):
    """
    License server to be updated in the database.
    """

    host: Optional[str] = None
    port: Optional[int] = None
    type: Optional[LicenseServerType] = None

    @validator("port")
    def port_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Port must be positive")
        return v


class LicenseServerResponse(BaseModel):
    """
    License server response from the database.
    """

    id: int
    host: str
    port: int
    type: LicenseServerType

    class Config:
        orm_mode = True


class Cluster(BaseModel):
    """
    Represents the clusters in a feature configuration.
    """

    id: int
    name: str
    client_id: str

    class Config:
        orm_mode = True


class Job(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_id: int
    cluster_id: int
    username: str
    lead_host: str

    class Config:
        orm_mode = True


class Product(BaseModel):
    """
    Represents a feature's product.
    """

    id: int
    name: str

    class Config:
        orm_mode = True


class Feature(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    id: int
    name: str
    product_id: int

    class Config:
        orm_mode = True


class Configuration(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_id: int
    grace_time: int

    class Config:
        orm_mode = True


class LicServConfigMapping(BaseModel):
    """
    Represents the many-to-many relationship between license servers and configs.
    """

    license_server_id: int
    config_id: int

    class Config:
        orm_mode = True


class Inventory(BaseModel):
    """
    Represents the inventory of a feature.
    """

    id: int
    feature_id: int
    total: int
    used: int
    booked: int
    available: int

    class Config:
        orm_mode = True


class Booking(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int
    job_id: int
    feature_id: int
    config_id: int
    quantity: int

    class Config:
        orm_mode = True
