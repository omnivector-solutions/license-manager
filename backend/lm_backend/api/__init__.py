from fastapi import APIRouter

from lm_backend.api.booking import router as router_booking
from lm_backend.api.config import router as router_config
from lm_backend.api.license import router as router_license

api_v1 = APIRouter()
api_v1.include_router(router_license, prefix="/license", tags=["License"])
api_v1.include_router(router_booking, prefix="/booking", tags=["Booking"])
api_v1.include_router(router_config, prefix="/config", tags=["Config"])
