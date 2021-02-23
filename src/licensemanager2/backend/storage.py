"""
Persistent data storage for the backend
"""
import databases
import sqlalchemy

from licensemanager2.backend.schema import metadata
from licensemanager2.backend.settings import SETTINGS


database = databases.Database(SETTINGS.DATABASE_URL)


def create_all_tables():
    """
    Create all the tables in the database
    """
    engine = sqlalchemy.create_engine(
        SETTINGS.DATABASE_URL,
    )

    metadata.create_all(engine)
