import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
import models

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, autoflush=False, autocommit=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield


async def get_db() -> AsyncSession:
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()


def format_user_response(user: models.User, skin_list: list):
    return {
        "id": str(user.id),
        "username": user.username,
        "balance": user.balance,
        "skins": skin_list,
        "createdAt": user.created_at.isoformat()
    }