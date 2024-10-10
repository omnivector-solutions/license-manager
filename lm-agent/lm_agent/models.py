from typing import List

from pydantic import BaseModel, Field, PositiveInt

from lm_agent.constants import LicenseServerType, PRODUCT_FEATURE_RX


class LicenseUsesItem(BaseModel):
    """
    A list of usage information for a license.
    """

    username: str
    lead_host: str
    booked: int


class LicenseReportItem(BaseModel):
    """
    An item in a LicenseReport, a count of tokens for one product/feature.
    """

    feature_id: int
    product_feature: str = Field(..., pattern=PRODUCT_FEATURE_RX)
    used: int
    total: int
    uses: List[LicenseUsesItem] = []


class ParsedFeatureItem(BaseModel):
    """
    A report of the parsed license server output.
    """

    feature: str
    total: int
    used: int
    uses: List[LicenseUsesItem] = []


class LicenseBooking(BaseModel):
    """
    Structure to represent a license booking.
    """

    product_feature: str = Field(..., pattern=PRODUCT_FEATURE_RX)
    quantity: int


class LicenseBookingRequest(BaseModel):
    """
    Structure to represent a list of license bookings.
    """

    slurm_job_id: str
    username: str
    lead_host: str
    bookings: List[LicenseBooking] = []


class ExtractedBookingSchema(BaseModel):
    """
    Represents the booking from a job with the job information extracted.
    """

    booking_id: int
    job_id: int
    slurm_job_id: str
    username: str
    lead_host: str
    feature_id: int
    quantity: int


class ExtractedUsageSchema(BaseModel):
    """
    Representes the usage lines extracted from a feature report.
    """

    feature_id: int
    username: str
    lead_host: str
    quantity: int


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
