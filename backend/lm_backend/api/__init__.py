from fastapi import APIRouter
from lm_backend.api.license_server.routes import router as router_license_server
from lm_backend.api.cluster.routes import router as router_cluster

api = APIRouter()
api.include_router(router_license_server, prefix="/license_servers", tags=["License Server"])
#api.include_router(router_cluster, prefix="/clusters", tags=["Cluster"])
