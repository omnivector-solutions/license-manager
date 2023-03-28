from fastapi import APIRouter

from lm_backend.api.routes.license_server import router as router_license_server

api = APIRouter()
api.include_router(router_license_server, prefix="/license_servers", tags=["License Server"])
