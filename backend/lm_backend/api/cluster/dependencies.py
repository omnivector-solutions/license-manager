from lm_backend.api.cluster.crud import ClusterCRUD
from lm_backend.database.storage import async_session


async def get_cluster_crud() -> ClusterCRUD:
    async with async_session() as session:
        async with session.begin():
            yield ClusterCRUD(async_session=session)
