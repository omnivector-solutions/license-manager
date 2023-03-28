"""Generic CRUD operations for SQLAlchemy models."""

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, TypeVar, Generic, Optional

from lm_backend.database.storage import Base
from lm_backend.api.api_schemas import BaseCreateSchema, BaseUpdateSchema


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseCreateSchema)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseUpdateSchema)


class CRUDGeneric(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: ModelType):
        self.model = model

    async def create(self, session: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        obj = self.model(**obj_in.dict())
        await session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        return await self.async_session.query(self.model).filter(self.model.id == id).first()

    async def get_all(self) -> List[ModelType]:
        return await self.async_session.query(self.model).all()

    async def update(
        self, id: int, obj_in: UpdateSchemaType
    ) -> Optional[ModelType]:
        obj = await self.async_session.query(self.model).filter(self.model.id == id).first()
        if not obj:
            return None
        for field in obj_in.dict(exclude_unset=True):
            setattr(obj, field, obj_in[field])
        self.async_session.add(obj)
        self.async_session.commit()
        self.async_session.refresh(obj)
        return obj

    async def delete(self, id: int) -> Optional[ModelType]:
        obj = self.async_session.query(self.model).filter(self.model.id == id).first()
        if not obj:
            return None
        self.async_session.delete(obj)
        self.async_session.commit()
        return obj
