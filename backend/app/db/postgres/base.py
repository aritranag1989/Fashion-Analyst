from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
# NullPool: never hold a connection open between uses. FastAPI/uvicorn runs one persistent event
# loop for its whole lifetime so real pooling would be safe there, but Celery tasks each wrap their
# work in a fresh asyncio.run() call - a pooled connection created in one task's event loop is dead
# by the time the next task's (new) event loop tries to reuse it ("Event loop is closed"). Since
# this engine is shared by both contexts, and local Postgres connection setup is effectively free,
# NullPool is the simplest fix that's correct for both rather than maintaining two engines.
engine = create_async_engine(settings.database_url, poolclass=NullPool)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
