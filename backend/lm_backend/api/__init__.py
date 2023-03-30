from fastapi import APIRouter

from lm_backend.api.clusters.routes import router as router_cluster
from lm_backend.api.license_servers.routes import router as router_license_server
from lm_backend.api.routes.configuration import router as router_configuration

api = APIRouter()
api.include_router(router_license_server, prefix="/license_servers", tags=["License Server"])
api.include_router(router_cluster, prefix="/clusters", tags=["Cluster"])
api.include_router(router_configuration, prefix="/configurations", tags=["Configuration"])
