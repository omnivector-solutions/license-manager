from typing import List

from pydantic import BaseModel, ConfigDict, model_validator


class LicenseInUseCreate(BaseModel):
    quantity: int
    user_name: str
    lead_host: str
    license_name: str


class LicenseInUseRow(LicenseInUseCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


class LicenseCreate(BaseModel):
    name: str
    total: int


class LicenseRow(LicenseCreate):
    in_use: int = 0
    licenses_in_use: List[LicenseInUseRow] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def calculate_in_use(self):
        self.in_use = sum(license_in_use.quantity for license_in_use in self.licenses_in_use)
        return self
