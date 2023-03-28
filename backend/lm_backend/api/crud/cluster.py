"""CRUD operations for clusters."""
from typing import List, Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.schemas.cluster import ClusterCreateSchema, ClusterUpdateSchema, ClusterSchema
from lm_backend.models.cluster import Cluster

from fastapi import HTTPException


class ClusterCRUD:
    """
    CRUD operations for clusters.
    """

    async def create(self, db_session: AsyncSession, cluster: ClusterCreateSchema) -> ClusterSchema:
        """
        Add a new cluster to the database.
        Returns the newly created cluster.
        """
        new_cluster = Cluster(**cluster.dict())
        try:
            await db_session.add(new_cluster)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Cluster could not be created")
        return ClusterSchema.from_orm(new_cluster)

    async def read(self, db_session: AsyncSession, cluster_id: int) -> Optional[ClusterSchema]:
        """
        Read a cluster with the given id.
        Returns the cluster or None if it does not exist.
        """
        query = await db_session.execute(select(Cluster).filter(Cluster.id == cluster_id))
        db_cluster = query.scalars().one_or_none()

        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")

        return ClusterSchema.from_orm(db_cluster.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[ClusterSchema]:
        """
        Read all clusters.
        Returns a list of clusters.
        """
        query = await db_session.execute(select(Cluster))
        db_clusters = query.scalars().all()
        return [ClusterSchema.from_orm(db_cluster) for db_cluster in db_clusters]

    async def update(
        self, db_session: AsyncSession, cluster_id: int, cluster_update: ClusterUpdateSchema
    ) -> Optional[ClusterSchema]:
        """
        Update a cluster in the database.
        Returns the updated cluster.
        """
        query = await db_session.execute(select(Cluster).filter(Cluster.id == cluster_id))
        db_cluster = query.scalar_one_or_none()

        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")

        for field, value in cluster_update:
            setattr(db_cluster, field, value)

        await db_session.commit()
        await db_session.refresh(db_cluster)
        return ClusterSchema.from_orm(db_cluster)

    async def delete(self, db_session: AsyncSession, cluster_id: int) -> bool:
        """
        Delete a cluster from the database.
        """
        query = await db_session.execute(select(Cluster).filter(Cluster.id == cluster_id))
        db_cluster = query.scalars().one_or_none()

        if db_cluster is None:
            raise HTTPException(status_code=404, detail="Cluster not found")
        try:
            db_session.delete(db_cluster)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Cluster could not be deleted")
