from fastapi import APIRouter

from lm_backend.api.routes.clusters import router as router_cluster
from lm_backend.api.routes.configurations import router as router_configuration
from lm_backend.api.routes.license_servers import router as router_license_server

api = APIRouter()
api.include_router(router_license_server, prefix="/license_servers", tags=["License Server"])
api.include_router(router_cluster, prefix="/clusters", tags=["Cluster"])
api.include_router(router_configuration, prefix="/configurations", tags=["Configuration"])
