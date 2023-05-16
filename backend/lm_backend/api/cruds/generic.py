"""Generic CRUD class for SQLAlchemy models."""
from typing import List, Optional, TypeVar, Union

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import Column, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import UnaryExpression

from lm_backend.api.models import Base
from lm_backend.api.schemas import BaseCreateSchema, BaseUpdateSchema
from lm_backend.database import search_clause, sort_clause

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
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Object could not be created.")

        await db_session.refresh(db_obj)
        await db_session.close()
        return db_obj

    async def filter(
        self, db_session: AsyncSession, filter_field: Column, filter_term: str
    ) -> Optional[ModelType]:
        """
        Filter an object using a filter field and filter term.
        Returns the object or raise an exception if it does not exist.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(select(self.model).filter(filter_field == filter_term))
                db_obj = query.scalars().one_or_none()
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Object could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail="Object not found.")

        return db_obj

    async def read(self, db_session: AsyncSession, id: int) -> Optional[ModelType]:
        """
        Read an object from the database with the given id.
        Returns the object or raise an exception if it does not exist.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(select(self.model).filter(self.model.id == id))
                db_obj = query.scalars().one_or_none()
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Object could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail="Object not found.")

        return db_obj

    async def read_all(
        self,
        db_session: AsyncSession,
        search: str = None,
        sort_field: Union[Column, UnaryExpression] = None,
        sort_ascending: bool = True,
    ) -> List[ModelType]:
        """
        Read all objects.
        Returns a list of objects.
        """
        async with db_session.begin():
            try:
                stmt = select(self.model)
                if search is not None:
                    stmt = stmt.where(search_clause(search, self.model.searchable_fields))
                if sort_field is not None:
                    stmt = stmt.order_by(sort_clause(sort_field, self.model.sortable_fields, sort_ascending))
                query = await db_session.execute(stmt)
                db_objs = query.scalars().all()
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Objects could not be read.")
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
                    raise HTTPException(status_code=404, detail="Object not found.")

                for field, value in obj:
                    if value is not None:
                        setattr(db_obj, field, value)
                await db_session.flush()
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Object could not be updated.")

            await db_session.refresh(db_obj)
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
                logger.error(e)
                raise HTTPException(status_code=400, detail="Object could not be deleted.")

            if db_obj is None:
                raise HTTPException(status_code=404, detail="Object not found.")

            try:
                await db_session.delete(db_obj)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail="Object could not be deleted.")
        await db_session.flush()
