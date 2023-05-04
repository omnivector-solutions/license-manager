"""
Session module to access the database.
"""
from asyncio import current_task

from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine

from lm_backend.config import settings

async_engine = create_async_engine(settings.DATABASE_URL)
async_session_factory = async_sessionmaker(bind=async_engine, expire_on_commit=False, class_=AsyncSession)

AsyncScopedSession = async_scoped_session(async_session_factory, scopefunc=current_task)


async def get_session() -> AsyncSession:
    """Create a new async session for each request."""
    async with AsyncScopedSession() as session:
        yield session
