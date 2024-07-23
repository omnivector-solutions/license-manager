from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from yarl import URL

from lm_simulator.config import settings
from lm_simulator.models import Base

engine = create_async_engine(
    str(
        URL.build(
            scheme="postgresql+asyncpg",
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PSWD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            path=f"/{settings.DATABASE_NAME}",
        )
    )
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
