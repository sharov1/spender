from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
#from .base import Base
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine
import os

from aiosqlite import *
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

#Users base
class User(Base):
    __tablename__ = "spenderbot_users"
    
    telegram_id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=True)
    firstname = Column(String(50), nullable=False)
    lastname = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    registred_at = Column(DateTime, default=datetime.now)


#User settings base
class UserSettings(Base):
    __tablename__ = "spenderbot_settings"

    user_id = mapped_column(Integer, ForeignKey("spenderbot_users.telegram_id"), primary_key=True)
    currency = mapped_column(String(10), default="$")
    categories = mapped_column(String(300), default="Food,Transport,Coffee,Gifts,Other")
    limit = mapped_column(Float, nullable=True)
    notifications = mapped_column(Boolean, default=True)



#Expenses base
class Expense(Base):
    __tablename__ = "spenderbot_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("spenderbot_users.telegram_id"))
    category: Mapped[str] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Float)
    created_at = mapped_column(DateTime, default=datetime.now)



engine = create_async_engine(
    os.getenv("SPENDER_DB_URL", "sqlite+aiosqlite:///spender.db"),
    echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# For manual start python db/models.py
if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
