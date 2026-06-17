from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import settings

Base = declarative_base()

# Async engine for the FastAPI API
async_engine = create_async_engine(settings.async_db_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Sync engine for the worker process (LangGraph nodes are sync)
sync_engine = create_engine(settings.sync_db_url, echo=False, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_models():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
