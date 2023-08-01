from fastapi import APIRouter

from lm_backend.api.routes.bookings import router as router_bookings
from lm_backend.api.routes.configurations import router as router_configurations
from lm_backend.api.routes.features import router as router_features
from lm_backend.api.routes.jobs import router as router_jobs
from lm_backend.api.routes.license_servers import router as router_license_servers
from lm_backend.api.routes.products import router as router_products

api = APIRouter()
api.include_router(router_configurations, prefix="/configurations", tags=["Configuration"])
api.include_router(router_license_servers, prefix="/license_servers", tags=["License Server"])
api.include_router(router_products, prefix="/products", tags=["Product"])
api.include_router(router_features, prefix="/features", tags=["Feature"])
api.include_router(router_jobs, prefix="/jobs", tags=["Job"])
api.include_router(router_bookings, prefix="/bookings", tags=["Booking"])
