"""Database session."""
from lm_backend.database.storage import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session() -> AsyncSession:
    """Create a new async session for each request."""
    async with async_sessionmaker() as session:
        yield session
