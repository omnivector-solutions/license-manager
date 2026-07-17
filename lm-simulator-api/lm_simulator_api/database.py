from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from yarl import URL

from lm_simulator_api.config import settings
from lm_simulator_api.models import Base


def get_database_url() -> str:
    """Build the database URL based on DATABASE_TYPE setting."""
    if settings.DATABASE_TYPE == "sqlite":
        # Ensure the directory exists for SQLite
        sqlite_path = Path(settings.SQLITE_PATH)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{settings.SQLITE_PATH}"
    else:
        # PostgreSQL
        return str(
            URL.build(
                scheme="postgresql+asyncpg",
                user=settings.DATABASE_USER,
                password=settings.DATABASE_PSWD,
                host=settings.DATABASE_HOST,
                port=settings.DATABASE_PORT,
                path=f"/{settings.DATABASE_NAME}",
            )
        )


# Build engine with appropriate settings for the database type
connect_args = {}
if settings.DATABASE_TYPE == "sqlite":
    # SQLite needs check_same_thread=False for async
    connect_args = {"check_same_thread": False}

engine = create_async_engine(get_database_url(), connect_args=connect_args)

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
