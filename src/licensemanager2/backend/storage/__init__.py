"""
Persistent data storage for the backend
"""
import os

import databases
import sqlalchemy

from licensemanager2.backend.storage.schema import metadata


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sqlite.db")
# DATABASE_URL = "postgresql://user:password@postgresserver/db"

database = databases.Database(DATABASE_URL)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)


def create_all_tables():
    """
    Create all the tables in the database
    """
    metadata.create_all(engine)
