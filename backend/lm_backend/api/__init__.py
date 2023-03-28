from fastapi import APIRouter
from lm_backend.api.license_server.routes import router as router_license_server

api = APIRouter()
api.include_router(router_license_server, prefix="/license_servers", tags=["License Server"])
