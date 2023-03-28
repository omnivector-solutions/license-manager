"""CRUD operations for clusters."""
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from lm_backend.api.cluster.schemas import ClusterCreateRequest, ClusterResponse
from lm_backend.database.models import Cluster


class ClusterCRUD:
    def __init__(self, async_session: Session):
        self.async_session = async_session

    async def create(self, cluster: ClusterCreateRequest) -> ClusterResponse:
        """
        Add a new cluster to the database.
        Returns the newly created cluster or False if creation fails.
        """
        new_cluster = Cluster(**cluster.dict())
        try:
            self.async_session.add(new_cluster)
            await self.async_session.flush()
        except Exception:
            return False
        return ClusterResponse.from_orm(new_cluster)

    async def read(self, cluster_id: int) -> Optional[ClusterResponse]:
        """
        Read a cluster with the given id.
        Returns the cluster or None if it does not exist.
        """
        query = await self.async_session.execute(
            select(Cluster).filter(Cluster.id == cluster_id)
        )
        cluster = query.scalar_one_or_none()

        if cluster is None:
            return None

        return ClusterResponse.from_orm(cluster)

    async def read_all(self) -> List[ClusterResponse]:
        """
        Read all clusters.
        Returns a list of clusters.
        """
        query = await self.async_session.execute(select(Cluster))
        clusters = query.scalars().all()
        return [ClusterResponse.from_orm(cluster) for cluster in clusters]

    async def update(self, cluster_id: int, name: Optional[str], client_id: Optional[str]) -> ClusterResponse:
        """
        Update a cluster in the database.
        Returns the updated cluster.
        """
        query = update(Cluster).where(Cluster.id == cluster_id)
        if name:
            query = query.values(name=name)
        if client_id:
            query = query.values(client_id=client_id)
        query.execution_options(synchronize_session="fetch")
        await self.async_session.execute(query)
        await self.async_session.flush()
        return await self.read(cluster_id)

    async def delete(self, cluster_id: int) -> bool:
        """
        Delete a cluster from the database.
        Returns True if the cluster was deleted, False otherwise.
        """
        query = delete(Cluster).where(Cluster.id == cluster_id)
        try:
            await self.async_session.execute(query)
            await self.async_session.flush()
        except Exception:
            return False
        return False
