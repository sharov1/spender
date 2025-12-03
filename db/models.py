from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
#from .base import Base
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine
import os

from aiosqlite import *
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "spenderbot_users"
    
    telegram_id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=True)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    registred_at = Column(DateTime, default=datetime.now)

engine = create_async_engine(
    os.getenv("SPENDER_DB_URL", "sqlite+aiosqlite:///spender.db"),
    echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Для ручного запуска файла: python db/models.py
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())


#class Expense(Base):
#    pass