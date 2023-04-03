"""
Schemas for the License Manager API.
Schemas:
    - Base:
        - BaseCreateSchema
        - BaseUpdateSchema
    - License Server:
        - LicenseServerType
        - LicenseServerCreateSchema
        - LicenseServerUpdateSchema
        - LicenseServerSchema
    - Cluster:
        - ClusterCreateSchema
        - ClusterUpdateSchema
        - ClusterSchema
    - Configuration:
        - ConfigurationCreateSchema
        - ConfigurationUpdateSchema
        - ConfigurationSchema
    - Product:
        - ProductCreateSchema
        - ProductUpdateSchema
        - ProductSchema
    - Feature:
        - FeatureCreateSchema
        - FeatureUpdateSchema
        - FeatureSchema
    - Inventory:
        - InventoryCreateSchema
        - InventoryUpdateSchema
        - InventorySchema
    - Job:
        - JobCreateSchema
        - JobUpdateSchema
        - JobSchema
    - Booking:
        - BookingCreateSchema
        - BookingUpdateSchema
        - BookingSchema
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, validator


class BaseCreateSchema(BaseModel):
    """
    Base class for creating objects in the database.
    """

    pass


class BaseUpdateSchema(BaseModel):
    """
    Base class for updating objects in the database.
    """

    pass


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

    config_id: int
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

    config_id: Optional[int] = None
    host: Optional[str] = None
    port: Optional[int] = None
    type: Optional[LicenseServerType] = None

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
    config_id: int
    host: str
    port: int
    type: LicenseServerType

    class Config:
        orm_mode = True


class InventoryCreateSchema(BaseCreateSchema):
    """
    Represents the inventory of a feature.
    """

    feature_id: int
    total: int
    used: int
    #booked: int
    #available: int


class InventoryUpdateSchema(BaseUpdateSchema):
    """
    Represents the inventory of a feature.
    """

    feature_id: int
    total: int
    used: int
    #booked: int
    #available: int


class InventorySchema(BaseModel):
    """
    Represents the inventory of a feature.
    """

    id: int
    feature_id: int
    total: int
    used: int
    #booked: int
    #available: int

    class Config:
        orm_mode = True


class ProductCreateSchema(BaseCreateSchema):
    """
    Represents a feature's product.
    """

    name: str


class ProductUpdateSchema(BaseUpdateSchema):
    name: str


class ProductSchema(BaseModel):
    """
    Represents a feature's product.
    """

    id: int
    name: str

    class Config:
        orm_mode = True


class BookingCreateSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    job_id: int
    feature_id: int
    quantity: int


class BookingUpdateSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    job_id: int
    feature_id: int
    quantity: int


class BookingSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int
    job_id: int
    feature_id: int
    quantity: int

    class Config:
        orm_mode = True


class FeatureCreateSchema(BaseCreateSchema):
    """
    Represents the features in a feature configuration.
    """

    name: str
    product_id: int
    config_id: int


class FeatureUpdateSchema(BaseUpdateSchema):
    """
    Represents the features in a feature configuration.
    """

    name: str
    product_id: int
    config_id: int


class FeatureSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    id: int
    name: str
    product_id: int
    config_id: int
    inventory: InventorySchema = None
    bookings: List[BookingSchema] = []

    class Config:
        orm_mode = True


class ConfigurationCreateSchema(BaseCreateSchema):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_id: int
    grace_time: int
    reserved: int


class ConfigurationUpdateSchema(BaseUpdateSchema):
    name: str
    cluster_id: int
    grace_time: int
    reserved: int


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_id: int
    features: List[FeatureSchema] = []
    license_servers: List[LicenseServerSchema] = []
    grace_time: int
    reserved: int

    class Config:
        orm_mode = True


class ClusterCreateSchema(BaseCreateSchema):
    """
    Clusters to be created in the database.
    """

    name: str
    client_id: str

    class Config:
        orm_mode = True


class ClusterUpdateSchema(BaseUpdateSchema):
    """
    Cluster to be updated in the database.
    """

    name: Optional[str] = None
    client_id: Optional[str] = None


class ClusterSchema(BaseModel):
    """
    Cluster response from the database.
    """

    id: int
    name: str
    client_id: str
    configurations: List[ConfigurationSchema] = None

    class Config:
        orm_mode = True


class JobCreateSchema(BaseCreateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: int
    cluster_id: int
    username: str
    lead_host: str


class JobUpdateSchema(BaseUpdateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: int
    cluster_id: int
    username: str
    lead_host: str


class JobSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    id: int
    slurm_job_id: int
    cluster_id: int
    username: str
    lead_host: str

    bookings: List[BookingSchema] = None

    class Config:
        orm_mode = True
