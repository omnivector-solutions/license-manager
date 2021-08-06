from fastapi import APIRouter, Depends, Header

from app.api.booking import router as router_booking
from app.api.config import router as router_config
from app.api.license import router as router_license
from app.debug import debug
from app.storage import database
from app.table_schemas import booking_table, config_table, license_table

api_v1 = APIRouter()
api_v1.include_router(router_license, prefix="/license", tags=["License"])
api_v1.include_router(router_booking, prefix="/booking", tags=["Booking"])
api_v1.include_router(router_config, prefix="/config", tags=["Config"])


@database.transaction()
@api_v1.put("/reset")
async def reset_everything(debug=Depends(debug), x_reset=Header(...)):
    """
    Reset all database data (only permitted in DEBUG mode)

    Set the header `X-Reset:` to anything you want.
    """
    await database.execute(license_table.delete())
    await database.execute(booking_table.delete())
    await database.execute(config_table.delete())
