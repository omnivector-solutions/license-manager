import re
import shutil
from typing import Any
from unittest.mock import patch

import sqlalchemy
from fastapi.exceptions import HTTPException
from pytest import fixture, raises

from lm_backend import storage
from lm_backend.table_schemas import config_table

_LIST_TABLES_SQL = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"


def query_stripper(query: Any):
    """
    Provide a small helper function that removes whitespace and applies lower-case to a query.

    Helpful for tests where we are matching strings with the same content that might be formatted differently.
    """
    return re.sub(r"\s+", "", str(query)).lower()


@fixture
def raw_connection(backend_client, tmpdir):
    """
    Create a connection to an empty temporary sqlite db
    """
    tmp_url = tmpdir / "sqlite.db"
    engine = sqlalchemy.create_engine(
        f"sqlite:///{tmp_url}",
    )
    yield engine.connect()
    shutil.rmtree(tmpdir)


def test_create_all_tables(raw_connection):
    """
    Does this result in new tables?
    """
    before = raw_connection.execute(_LIST_TABLES_SQL)
    assert len(list(before)) == 0
    with patch.object(storage.settings, "DATABASE_URL", str(raw_connection.engine.url)):
        storage.create_all_tables()
    after = raw_connection.execute(_LIST_TABLES_SQL)
    assert len(list(after)) == 3


def test_search_clause__produces_valid_query():
    """
    Does the ``search_clause()`` function properly add search to a sql query?
    """
    query = config_table.select().where(
        storage.search_clause(
            search_terms="foo",
            searchable_fields=[
                config_table.c.name,
                config_table.c.product,
            ],
        )
    )

    rendered_query = storage.render_sql(query)
    columns_str = ",".join([str(c) for c in config_table.columns])
    assert query_stripper(rendered_query) == query_stripper(
        f"""
        select {columns_str}
        from config
        where
            lower(config.name) like lower('%foo%')
            or lower(config.product) like lower('%foo%')
        """
    )


def test_sort_clause__produces_valid_query():
    """
    Does the ``sort_clause()`` function properly add sort to a sql query?
    """

    query = config_table.select().order_by(
        storage.sort_clause(
            sort_field="name",
            sortable_fields=[
                config_table.c.name,
                config_table.c.product,
            ],
            sort_ascending=False,
        )
    )

    rendered_query = storage.render_sql(query)
    columns_str = ",".join([str(c) for c in config_table.columns])
    assert query_stripper(rendered_query) == query_stripper(
        f"""
        select {columns_str}
        from config
        order by
            config.name desc
        """
    )


def test_sort_clause__produces_valid_query():
    """
    Does the ``sort_clause()`` function raise an exception if selected
    sort field is not in the list of sortable fields?
    """

    with raises(HTTPException) as exc_info:
        storage.sort_clause(
            sort_field="foo",
            sortable_fields=[
                config_table.c.name,
                config_table.c.product,
            ],
            sort_ascending=False,
        )
    assert "Invalid sorting column requested: foo" in exc_info.value.detail
