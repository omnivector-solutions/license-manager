from pydantic import BaseModel, ConfigDict

from lm_simulator_api.constants import LicenseServerType


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
    license_server_type: LicenseServerType


class LicenseRow(LicenseCreate):
    in_use: int = 0
    licenses_in_use: list[LicenseInUseRow] = []

    model_config = ConfigDict(from_attributes=True)
