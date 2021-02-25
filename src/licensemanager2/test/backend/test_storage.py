"""
Low-level storage tests
"""
import shutil
from unittest.mock import patch

from pytest import fixture
import sqlalchemy

from licensemanager2.backend import storage


_LIST_TABLES_SQL = (
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
)


@fixture
def raw_connection(tmpdir):
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
    with patch.object(storage.SETTINGS, "DATABASE_URL", str(raw_connection.engine.url)):
        storage.create_all_tables()
    after = raw_connection.execute(_LIST_TABLES_SQL)
    assert len(list(after)) == 2
