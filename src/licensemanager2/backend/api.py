"""
Endpoints for the backend
"""
from fastapi import APIRouter, Depends, Header

from licensemanager2.backend.booking import router_booking
from licensemanager2.backend.debug import debug
from licensemanager2.backend.license import router_license
from licensemanager2.backend.configuration import router_config
from licensemanager2.backend.schema import booking_table, license_table, config_table
from licensemanager2.backend.storage import database
from licensemanager2.common_api import OK


api_v1 = APIRouter()
api_v1.include_router(router_license, prefix="/license", tags=["License"])
api_v1.include_router(router_booking, prefix="/booking", tags=["Booking"])
api_v1.include_router(router_config, prefix="/config", tags=["Config"])


@database.transaction()
@api_v1.put("/reset", response_model=OK)
async def reset_everything(debug=Depends(debug), x_reset=Header(...)):
    """
    Reset all database data (only permitted in DEBUG mode)

    Set the header `X-Reset:` to anything you want.
    """
    await database.execute(license_table.delete())
    await database.execute(booking_table.delete())
    await database.execute(config_table.delete())
    return OK()
