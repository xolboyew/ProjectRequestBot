"""Async engine va sessiya fabrikasi (SQLite yoki PostgreSQL)."""
from __future__ import annotations

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from database.models import Base


def _build_engine():
    url = make_url(settings.database_url)
    connect_args: dict = {}
    if url.drivername.startswith("postgresql"):
        query = dict(url.query)
        sslmode = query.pop("sslmode", None)
        query.pop("channel_binding", None)  # Neon qo'shadi, asyncpg tanimaydi
        url = url.set(query=query)
        if sslmode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = "require"
        return create_async_engine(url, pool_pre_ping=True, connect_args=connect_args)
    return create_async_engine(url)


engine = _build_engine()
session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
