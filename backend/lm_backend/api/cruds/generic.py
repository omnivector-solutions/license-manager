"""Generic CRUD class for SQLAlchemy models."""
from typing import List, Optional, TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from lm_backend.api.schemas import BaseCreateSchema, BaseUpdateSchema
from lm_backend.database import Base

# from sqlalchemy.orm import expression


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseCreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseUpdateSchema)


class GenericCRUD:
    def __init__(self, model: ModelType, create_schema: CreateSchemaType, update_schema: UpdateSchemaType):
        """Initializes the CRUD class with the model to be used."""
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema

    async def create(self, db_session: AsyncSession, obj: CreateSchemaType) -> ModelType:
        """Creates a new object in the database."""
        db_obj = self.model(**obj.dict())
        try:
            async with db_session.begin():
                db_session.add(db_obj)
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Object could not be created: {e}")
        return db_obj

    async def read(self, db_session: AsyncSession, id: int, options=None) -> Optional[ModelType]:
        """
        Read an object from the database with the given id.
        Returns the object or raise an exception if it does not exist.
        """
        async with db_session.begin():
            try:
                if options is not None:
                    query = await db_session.execute(
                        select(self.model).options(options).filter(self.model.id == id)
                    )
                else:
                    query = await db_session.execute(select(self.model).filter(self.model.id == id))
                db_obj = query.scalars().one_or_none()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Object could not be read: {e}")

        if db_obj is None:
            raise HTTPException(status_code=404, detail="Object not found")

        return db_obj

    async def read_all(self, db_session: AsyncSession, options=None) -> List[ModelType]:
        """
        Read all objects.
        Returns a list of objects.
        """
        async with db_session.begin():
            try:
                if options is not None:
                    query = await db_session.execute(select(self.model).options(options))
                else:
                    query = await db_session.execute(select(self.model))
                db_objs = query.scalars().all()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Objects could not be read: {e}")
        return [db_obj for db_obj in db_objs]

    async def update(
        self,
        db_session: AsyncSession,
        id: int,
        obj: UpdateSchemaType,
    ) -> Optional[ModelType]:
        """
        Update an object in the database.
        Returns the updated object.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(select(self.model).filter(self.model.id == id))
                db_obj = query.scalar_one_or_none()

                if db_obj is None:
                    raise HTTPException(status_code=404, detail="Object not found")

                for field, value in obj:
                    if value is not None:
                        setattr(db_obj, field, value)
                await db_session.flush()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Object could not be updated: {e}")
        return db_obj

    async def delete(self, db_session: AsyncSession, id: int) -> bool:
        """
        Delete an object from the database.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(select(self.model).filter(self.model.id == id))
                db_obj = query.scalar_one_or_none()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Object could not be deleted: {e}")

            if db_obj is None:
                raise HTTPException(status_code=404, detail="Object not found")

            try:
                await db_session.delete(db_obj)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Obj could not be deleted: {e}")
        await db_session.flush()

    # async def query(self, db_session: AsyncSession, query_to_execute: expression) -> List[ModelType]:
    #     """
    #     Query the database for objects.
    #     Returns a list of objects.
    #     """
    #     async with db_session.begin():
    #         try:
    #             query = await db_session.execute(query_to_execute)
    #             db_objs = query.scalars().all()
    #         except Exception as e:
    #             raise HTTPException(status_code=400, detail=f"Objects could not be read: {e}")
    #     return [db_obj for db_obj in db_objs]


async def run_query(db_session: AsyncSession, query_to_execute) -> List[ModelType]:
    """
    Query the database for objects.
    Returns a list of objects.
    """
    async with db_session.begin():
        try:
            query = db_session.execute(query_to_execute)
            db_objs = query.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Objects could not be read: {e}")
        return [db_obj for db_obj in db_objs]
