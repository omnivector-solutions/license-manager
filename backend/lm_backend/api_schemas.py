"""
API request and response schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class ConfigurationRow(BaseModel):
    """
    A configuration row.
    """

    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    product: str
    features: str
    license_servers: List[str]
    license_server_type: str
    grace_time: int
    client_id: str

    class Config:
        orm_mode = True


class ConfigurationItem(BaseModel):
    """
    A configuration parsed item.
    """

    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    product: str
    features: dict
    license_servers: List[str]
    license_server_type: str
    grace_time: int
    client_id: str

    class Config:
        orm_mode = True


PRODUCT_FEATURE_RX = r"^.+?\..+$"


class BookingFeature(BaseModel):
    """
    One booked count for a single product.feature in a booking
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    booked: int

    class Config:
        orm_mode = True


class Booking(BaseModel):
    """
    A booking for a jobid with a list of the features it requests
    """

    job_id: str
    features: List[BookingFeature]
    lead_host: str
    user_name: str
    cluster_name: str

    class Config:
        orm_mode = True


class BookingRow(BaseModel):
    """
    A flattened booking, suitable to be inserted into the database
    """

    id: Optional[int] = Field(None)
    job_id: str
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    booked: int
    config_id: int
    lead_host: str
    user_name: str
    cluster_name: str

    class Config:
        orm_mode = True


class BookingRowDetail(BookingRow):
    """
    A booking row with more detail
    """

    created_at: Optional[datetime]
    config_name: Optional[str]

    class Config:
        orm_mode = True


class LicenseUseBase(BaseModel):
    """
    Used/Total counts for a product.feature license category
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    used: int


class LicenseUseReconcile(LicenseUseBase):
    """
    A reconcile [PATCH] Used/Total counts for a product.feature license category

    For creating items through the reconcile mechanism
    """

    total: int


class LicenseUseReconcileRequest(LicenseUseReconcile):
    """
    Used in the /reconcile request.
    """

    used_licenses: List


class LicenseUse(LicenseUseBase):
    """
    Used/Available/Total counts for a product.feature license category

    Returned by GET queries, including `available` for convenience
    """

    total: int

    available: Optional[int]

    @validator("available", always=True)
    def validate_available(cls, value, values):
        """
        Set available as a function of the other fields
        """
        return values["total"] - values["used"]


class LicenseUseWithBooking(LicenseUseBase):
    """
    Used/Available/Booked/Total counts for a product.feature license category.

    Returned by GET queries, including `available` for convenience.
    """

    total: int
    booked: Optional[int]
    available: Optional[int]

    @validator("available", always=True)
    def validate_available(cls, value, values):
        """
        Set available as a function of the other fields
        """
        return values["total"] - (values["used"] + values["booked"])


class LicenseUseBooking(LicenseUseBase):
    """
    A booking [PUT] object, specifying how many tokens are needed and no total
    """
