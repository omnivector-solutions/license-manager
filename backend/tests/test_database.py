import re
import shutil
from typing import Any
from unittest.mock import patch

import sqlalchemy
from fastapi.exceptions import HTTPException
from pytest import fixture, raises
from sqlalchemy import select

from lm_backend import database
from lm_backend.api.models import Product

_LIST_TABLES_SQL = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"


def query_stripper(query: Any):
    """
    Provide a small helper function that removes whitespace and applies lower-case to a query.

    Helpful for tests where we are matching strings with the same content that might be formatted differently.
    """
    return re.sub(r"\s+", "", str(query)).lower()


def test_search_clause__produces_valid_query():
    """
    Does the ``search_clause()`` function properly add search to a sql query?
    """
    query = select(Product).where(
        database.search_clause(
            search_terms="foo",
            searchable_fields=[
                Product.name,
            ],
        )
    )

    rendered_query = database.render_sql(query)
    columns = Product.__table__.columns.keys()
    columns_str = ",".join(["products." + c for c in columns])
    assert query_stripper(rendered_query) == query_stripper(
        f"""
        select {columns_str}
        from products
        where
            lower(products.name) like lower('%foo%')
        """
    )


def test_sort_clause__produces_valid_query():
    """
    Does the ``sort_clause()`` function properly add sort to a sql query?
    """

    query = select(Product).order_by(
        database.sort_clause(
            sort_field="name",
            sortable_fields=[
                Product.name,
            ],
            sort_ascending=False,
        )
    )

    rendered_query = database.render_sql(query)
    columns = Product.__table__.columns.keys()
    columns_str = ",".join(["products." + c for c in columns])
    assert query_stripper(rendered_query) == query_stripper(
        f"""
        select {columns_str}
        from products
        order by
            products.name desc
        """
    )


def test_sort_clause__raises_exception_for_invalid_sort_field():
    """
    Does the ``sort_clause()`` function raise an exception if selected
    sort field is not in the list of sortable fields?
    """

    with raises(HTTPException) as exc_info:
        database.sort_clause(
            sort_field="foo",
            sortable_fields=[
                Product.name,
            ],
            sort_ascending=False,
        )
    assert "Invalid sorting column requested: foo" in exc_info.value.detail
