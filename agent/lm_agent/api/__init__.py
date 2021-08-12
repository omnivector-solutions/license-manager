from fastapi import APIRouter

from lm_agent.api.booking_proxy import router as booking_proxy_router
from lm_agent.api.license_proxy import router as license_proxy_router

api_v1 = APIRouter()

api_v1.include_router(license_proxy_router, prefix="/license", tags=["License"])
api_v1.include_router(booking_proxy_router, prefix="/booking", tags=["Booking"])
