from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Cluster, Configuration
from lm_backend.database import get_session


class ClusterCRUD(GenericCRUD):
    def __init__(self, model, create_schema, update_schema):
        super().__init__(model, create_schema, update_schema)

    async def read_all(self, db_session: AsyncSession):
        async with db_session.begin():
            query = select(self.model).options(selectinload(self.model.configurations))
            result = await db_session.execute(query)
            return result.scalars().all()

    async def read(self, db_session: AsyncSession, id: int):
        async with db_session.begin():
            result = await db_session.execute(
                select(self.model)
                .options(
                    selectinload(self.model.configurations),
                )
                .where(self.model.id == id)
            )
            cluster = result.scalars().first()
            if not cluster:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
            return cluster

    async def delete(self, db_session: AsyncSession, id: int):
        async with db_session.begin():
            result = await db_session.execute(select(self.model).where(self.model.id == id))
            cluster = result.scalars().first()
            if not cluster:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
            await db_session.delete(cluster)
            await db_session.commit()
            return cluster
