from typing import List

from pydantic import BaseModel, Field, PositiveInt

from lm_agent.backend_utils.constants import LicenseServerType
from lm_agent.config import PRODUCT_FEATURE_RX


class LicenseServerSchema(BaseModel):
    """
    License server response from the database.
    """

    id: int
    config_id: int
    host: str
    port: PositiveInt


class ProductSchema(BaseModel):
    """
    Represents a feature's product.
    """

    id: int
    name: str


class FeatureSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    id: int
    name: str
    product: ProductSchema
    config_id: int
    reserved: int
    total: int
    used: int
    booked_total: int


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_client_id: str
    features: List[FeatureSchema] = []
    license_servers: List[LicenseServerSchema] = []
    grace_time: int
    type: LicenseServerType


class BookingSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int
    job_id: int
    feature_id: int
    quantity: int


class JobSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    id: int
    slurm_job_id: str
    cluster_client_id: str
    username: str
    lead_host: str

    bookings: List[BookingSchema] = []


class LicenseBooking(BaseModel):
    """
    Structure to represent a license booking.
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    quantity: int


class LicenseBookingRequest(BaseModel):
    """
    Structure to represent a list of license bookings.
    """

    slurm_job_id: int
    username: str
    lead_host: str
    bookings: List[LicenseBooking] = []
