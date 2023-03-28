"""Database session."""
from lm_backend.database.storage import AsyncSession


def async_session():
    """Return a new async session."""
    async_session = AsyncSession()
    try:
        yield async_session
    finally:
        async_session.close()
