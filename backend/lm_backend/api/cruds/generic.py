"""Generic CRUD class for SQLAlchemy models."""
from typing import Any, Generic, List, Optional, Protocol, Type, TypeVar, Union

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import Column, ColumnElement, and_, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, selectinload

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.database import search_clause, sort_clause


class CrudModelProto(Protocol):
    id: Mapped[int]
    searchable_fields: List[Column[Any]]
    sortable_fields: List[Column[Any]]
    __name__: str


CrudModel = TypeVar("CrudModel", bound=CrudModelProto)


class _GenericCRUD(Generic[CrudModel]):
    """Generic CRUD module to interface with database, to be utilized by all models."""

    def __init__(self, model: Type[CrudModel]):
        """Initializes the CRUD class with the model to be used."""
        self.model = model

    async def create(self, db_session: AsyncSession, obj: BaseCreateSchema) -> CrudModel:
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
    ) -> List[CrudModel]:
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
    ) -> Optional[CrudModel]:
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
    ) -> List[CrudModel]:
        """
        Read all objects.
        Returns a list of objects.
        """
        try:
            stmt = select(self.model)
            for relationship in inspect(self.model, raiseerr=True).relationships:
                stmt = stmt.options(selectinload(relationship))
            if search is not None:
                stmt = stmt.where(search_clause(search, self.model.searchable_fields))
            if sort_field is not None:
                stmt = stmt.order_by(sort_clause(sort_field, self.model.sortable_fields, sort_ascending))
            query = await db_session.scalars(stmt)
            db_objs = list(query.all())
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__}s could not be read.")
        return db_objs

    async def update(
        self,
        db_session: AsyncSession,
        id: Union[Column[int], int],
        obj: BaseUpdateSchema,
    ) -> Optional[CrudModel]:
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


class GenericCRUD(_GenericCRUD):
    """
    For some reason, Mypy does not allow you to use the _GenericCRUD class directly without a bunch of type
    errors like this:

    lm_backend/api/routes/license_servers.py:19: error: Value of type variable "CrudModel" of "GenericCRUD" cannot be "LicenseServer"  [type-var]  # noqa
        crud_license_server = GenericCRUD(LicenseServer)
                              ^~~~~~~~~~~~~~~~~~~~~~~~~~
    Adding a single additional level of inheritance with an empty derived class fixes the issue. ¯\_(ツ)_/¯
    """
