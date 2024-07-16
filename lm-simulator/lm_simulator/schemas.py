from typing import List, Optional

from pydantic import BaseModel, ConfigDict, model_validator


class LicenseInUseCreate(BaseModel):
    quantity: int
    user_name: str
    lead_host: str
    license_name: str


class LicenseInUseRow(LicenseInUseCreate):
    id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class LicenseCreate(BaseModel):
    name: str
    total: int


class LicenseRow(LicenseCreate):
    """Model for the license in the database, we calculate the in_use value dynamically."""

    id: Optional[int] = None
    licenses_in_use: List[LicenseInUseRow] = []
    # This is used to calculate the in_use value using the licenses_in_use field.
    in_use: Optional[int] = 0

    @model_validator(mode="after")
    def in_use_validator(self) -> int:
        """This validator is used to calculate the in_use value."""
        self.in_use = 0
        for license_in_use in self.licenses_in_use:
            self.in_use += license_in_use.quantity
        return self

    model_config = ConfigDict(from_attributes=True)
