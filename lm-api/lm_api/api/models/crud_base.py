from typing import Any, List

from inflection import tableize
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, MappedColumn, declared_attr, mapped_column


class Base(DeclarativeBase):
    pass


class CrudBase(Base):
    __abstract__ = True  # Mark this class as abstract to avoid creating a table

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """
        Dynamically create table name based on the class name.
        """
        return tableize(cls.__name__)

    id = mapped_column(Integer, primary_key=True)

    sortable_fields: List[MappedColumn[Any]] = []
    searchable_fields: List[MappedColumn[Any]] = []


class CrudWithoutId(CrudBase):
    __abstract__ = True

    @declared_attr.directive
    @classmethod
    def id(cls):
        return None
