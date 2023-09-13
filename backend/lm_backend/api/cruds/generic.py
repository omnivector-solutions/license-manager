"""Generic CRUD class for SQLAlchemy models."""
from asyncio import gather
from typing import List, Optional, Type, TypeVar, Union

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import Column, ColumnElement, and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.database import Base, search_clause, sort_clause

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseCreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseUpdateSchema)


class GenericCRUD:
    """Generic CRUD module to interface with database, to be utilized by all models."""

    def __init__(
        self,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
    ):
        """Initializes the CRUD class with the model to be used."""
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema

    async def create(self, db_session: AsyncSession, obj: CreateSchemaType) -> ModelType:
        """Creates a new object in the database."""
        db_obj = self.model(**obj.dict())
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
    ) -> List[ModelType]:
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
    ) -> Optional[ModelType]:
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
        search: str = None,
        sort_field: Optional[str] = None,
        sort_ascending: bool = True,
        force_refresh: bool = False,
    ) -> List[ModelType]:
        """
        Read all objects.
        Returns a list of objects.

        Note: The ``force_refresh`` parameter may be useful to force the gathered results to lazily load
              relationships or other computed fields like column properties or hybrid attributes.
        """
        try:
            stmt = select(self.model)
            if search is not None:
                stmt = stmt.where(search_clause(search, self.model.searchable_fields))
            if sort_field is not None:
                stmt = stmt.order_by(sort_clause(sort_field, self.model.sortable_fields, sort_ascending))
            query = await db_session.scalars(stmt)
            db_objs = list(query.all())
            if force_refresh:
                await gather(*(db_session.refresh(db_obj) for db_obj in db_objs))
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__}s could not be read.")
        return db_objs

    async def update(
        self,
        db_session: AsyncSession,
        id: Union[Column[int], int],
        obj: UpdateSchemaType,
    ) -> Optional[ModelType]:
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
