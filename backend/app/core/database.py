from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def _async_engine_kwargs(url: str) -> dict:
    if "sqlite" in url:
        return {}
    return {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}


def get_sync_engine_kwargs(url: str) -> dict:
    if "sqlite" in url:
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **_async_engine_kwargs(settings.DATABASE_URL),
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
