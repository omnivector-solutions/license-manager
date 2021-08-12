"""
Persistent data storage for the backend
"""
import databases
import sqlalchemy

from lm_backend.config import settings
from lm_backend.table_schemas import metadata

database = databases.Database(settings.DATABASE_URL)


def create_all_tables():
    engine = sqlalchemy.create_engine(settings.DATABASE_URL)
    metadata.create_all(engine)
