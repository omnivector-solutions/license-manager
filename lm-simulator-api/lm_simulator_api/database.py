from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from yarl import URL

from lm_simulator_api.config import settings
from lm_simulator_api.models import Base

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
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
