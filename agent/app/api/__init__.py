from fastapi import APIRouter

from app.api.booking_proxy import router as booking_proxy_router
from app.api.license_proxy import router as license_proxy_router

api_v1 = APIRouter()

api_v1.include_router(license_proxy_router, prefix="/license", tags=["License"])
api_v1.include_router(booking_proxy_router, prefix="/booking", tags=["Booking"])
