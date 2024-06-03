from typing import List, Optional

from pydantic import BaseModel, root_validator


class LicenseInUseCreate(BaseModel):
    quantity: int
    user_name: str
    lead_host: str
    license_name: str


class LicenseInUseRow(LicenseInUseCreate):
    id: Optional[int] = None

    class Config:
        orm_mode = True


class LicenseCreate(BaseModel):
    name: str
    total: int


class LicenseRow(LicenseCreate):
    """Model for the license in the database, we calculate the in_use value dynamically."""

    id: Optional[int] = None
    licenses_in_use: List[LicenseInUseRow] = []
    # This is used to calculate the in_use value using the licenses_in_use field.
    in_use: Optional[int] = 0

    @root_validator()
    def in_use_validator(cls, values) -> int:
        """This validator is used to calculate the in_use value."""
        values["in_use"] = 0
        for license_in_use in values["licenses_in_use"]:
            values["in_use"] += license_in_use.quantity
        return values

    class Config:
        orm_mode = True
