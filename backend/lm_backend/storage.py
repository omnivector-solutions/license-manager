"""
Persistent data storage for the backend
"""
import typing

import databases
import sqlalchemy
from fastapi.exceptions import HTTPException
from sqlalchemy import Column, or_
from sqlalchemy.sql.expression import BooleanClauseList, UnaryExpression
from starlette import status

from lm_backend.config import settings
from lm_backend.table_schemas import metadata

database = databases.Database(settings.DATABASE_URL)


def create_all_tables():
    engine = sqlalchemy.create_engine(settings.DATABASE_URL)
    metadata.create_all(engine)


def render_sql(query) -> str:
    """
    Render a sqlalchemy query into a string for debugging.
    """
    return query.compile(dialect=database._backend._dialect, compile_kwargs={"literal_binds": True})


def search_clause(
    search_terms: str,
    searchable_fields: typing.List[Column],
) -> BooleanClauseList:
    """
    Create search clause across searchable fields with search terms.
    """
    return or_(*[field.ilike(f"%{term}%") for field in searchable_fields for term in search_terms.split()])


def sort_clause(
    sort_field: str,
    sortable_fields: typing.List[Column],
    sort_ascending: bool,
) -> typing.Union[Column, UnaryExpression]:
    """
    Create a sort clause given a sort field, the list of sortable fields, and a sort_ascending flag.
    """
    sort_field_names = [f.name for f in sortable_fields]
    try:
        index = sort_field_names.index(sort_field)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid sorting column requested: {sort_field}. Must be one of {sort_field_names}",
        )
    sort_column: typing.Union[Column, UnaryExpression] = sortable_fields[index]
    if not sort_ascending:
        sort_column = sort_column.desc()
    return sort_column
