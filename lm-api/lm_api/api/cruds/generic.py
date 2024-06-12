"""Generic CRUD class for SQLAlchemy models."""
from __future__ import annotations

from typing import List, Optional, Sequence, Type, Union

from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import Column, ColumnElement, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_api.api.models.crud_base import CrudBase
from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_api.database import search_clause, sort_clause


class GenericCRUD:
    """Generic CRUD module to interface with database, to be utilized by all models."""

    def __init__(self, model: Type[CrudBase]):
        """Initializes the CRUD class with the model to be used."""
        self.model = model

    async def create(self, db_session: AsyncSession, obj: BaseCreateSchema) -> CrudBase:
        """Creates a new object in the database."""
        db_obj = self.model(**obj.model_dump())
        try:
            db_session.add(db_obj)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be created.")

        # TODO: Determine if the session actually needs to be flushed here. I think it might not
        await db_session.flush()
        await db_session.refresh(db_obj)
        return db_obj

    async def filter(
        self, db_session: AsyncSession, filter_expressions: List[ColumnElement[bool]]
    ) -> List[CrudBase]:
        """
        Filter objects using a filter field and filter term.
        Returns the list of objects or raise an exception if it does not exist.
        """
        try:
            query = await db_session.execute(select(self.model).filter(and_(*filter_expressions)))
            db_objs = list(query.scalars().all())
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be read.")

        if db_objs is None:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")

        return db_objs

    async def read(
        self, db_session: AsyncSession, id: Union[Column[int], int], force_refresh: bool = False
    ) -> Optional[CrudBase]:
        """
        Read an object from the database with the given id.
        Returns the object or raise an exception if it does not exist.
        """
        try:
            query = await db_session.execute(select(self.model).filter(self.model.id == id))
            db_obj = query.scalars().one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")

        if force_refresh:
            await db_session.refresh(db_obj)

        return db_obj

    async def read_all(
        self,
        db_session: AsyncSession,
        search: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_ascending: bool = True,
    ) -> Sequence[Union[CrudBase, BaseModel]]:
        """
        Read all objects.
        Returns a list of objects.
        """
        try:
            stmt = select(self.model)
            if search is not None:
                stmt = stmt.where(search_clause(search, self.model.searchable_fields))
            if sort_field is not None:
                stmt = stmt.order_by(sort_clause(sort_field, self.model.sortable_fields, sort_ascending))
            query = await db_session.scalars(stmt)
            return query.all()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__}s could not be read.")

    async def update(
        self,
        db_session: AsyncSession,
        id: Union[Column[int], int],
        obj: BaseUpdateSchema,
    ) -> Optional[CrudBase]:
        """
        Update an object in the database.
        Returns the updated object.
        """
        try:
            query = await db_session.execute(select(self.model).filter(self.model.id == id))
            db_obj = query.scalar_one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be updated.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")

        if all(value is None for _, value in obj):
            raise HTTPException(
                status_code=400, detail=f"Please provide a valid field to update {self.model.__name__}."
            )

        for field, value in obj:
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)

        try:
            await db_session.flush()
            await db_session.refresh(db_obj)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be updated.")

        return db_obj

    async def delete(self, db_session: AsyncSession, id: Union[Column[int], int]):
        """
        Delete an object from the database.
        """
        try:
            query = await db_session.execute(select(self.model).filter(self.model.id == id))
            db_obj = query.scalar_one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be deleted.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")

        try:
            await db_session.delete(db_obj)
            await db_session.flush()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be deleted.")

        return {"message": f"{self.model.__name__} deleted successfully."}
