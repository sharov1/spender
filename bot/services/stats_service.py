from sqlalchemy import select, func
from db.models import async_session, Expense
from datetime import datetime, timedelta


async def get_stats(user_id: int, start_date: datetime, end_date: datetime):
    """Базовая универсальная функция получения статистики"""

    async with async_session() as session:
        query = (
            select(
                Expense.category,
                func.sum(Expense.amount).label("total")
            )
            .where(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date < end_date,
            )
            .group_by(Expense.category)
        )

        rows = await session.execute(query)
        return rows.all()


async def get_today_stats(user_id: int):
    today = datetime.now().date()
    return await get_stats(
        user_id=user_id,
        start_date=datetime.combine(today, datetime.min.time()),
        end_date=datetime.combine(today + timedelta(days=1), datetime.min.time())
    )


async def get_week_stats(user_id: int):
    today = datetime.now().date()
    start = today - timedelta(days=7)

    return await get_stats(
        user_id=user_id,
        start_date=datetime.combine(start, datetime.min.time()),
        end_date=datetime.combine(today + timedelta(days=1), datetime.min.time())
    )
