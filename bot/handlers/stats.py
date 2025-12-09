from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
import datetime
from db.models import async_session, Expense, UserSettings

router = Router()

# ======================================================
#                    UI BUTTONS
# ======================================================

def stats_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📅 Сегодня", callback_data="stats:day"),
                InlineKeyboardButton(text="📆 Неделя", callback_data="stats:week")
            ],
            [
                InlineKeyboardButton(text="🗓 Месяц", callback_data="stats:month"),
                InlineKeyboardButton(text="📈 Год", callback_data="stats:year")
            ],
        ]
    )


def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="stats:back")]]
    )


# ======================================================
#                 GRAPH (ASCII)
# ======================================================

def bar_chart(value, max_value, length=15):
    if max_value == 0:
        return ""
    filled = int((value / max_value) * length)
    return "█" * filled + "░" * (length - filled)


# ======================================================
#        Display stats by categories
# ======================================================

def render_category_stats(expenses, currency):
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not categories:
        return "Нет данных."

    max_value = max(categories.values())
    lines = ["📦 *По категориям:*", ""]

    for name, value in categories.items():
        bar = bar_chart(value, max_value)
        lines.append(f"{name}: `{bar}` — *{value:.2f}{currency}*")

    return "\n".join(lines)


# ======================================================
#        Dynamic of the expenses by dates
# ======================================================

def render_daily_dynamics(expenses, currency):
    days = {}
    for e in expenses:
        d = e.created_at.date()
        days[d] = days.get(d, 0) + e.amount

    if not days:
        return "Нет данных."

    max_value = max(days.values())
    lines = ["📈 *Динамика:*", ""]

    for date, value in sorted(days.items()):
        bar = bar_chart(value, max_value)
        lines.append(f"{date}: `{bar}` {value:.2f}{currency}")

    return "\n".join(lines)


# ======================================================
#         Getting the data by periods of time
# ======================================================

async def get_expenses_by_period(user_id: int, period: str):
    now = datetime.datetime.now()

    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    elif period == "week":
        start = now - datetime.timedelta(days=now.weekday())

    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    else:
        start = now - datetime.timedelta(days=7)

    async with async_session() as session:
        result = await session.execute(
            select(Expense).where(
                Expense.user_id == user_id,
                Expense.created_at >= start
            )
        )
        return result.scalars().all(), start, now


# ======================================================
#                     /stats
# ======================================================

@router.message(Command("stats"))
async def stats_cmd(message: types.Message):
    await message.answer(
        "📊 *Выберите период статистики:*",
        reply_markup=stats_menu_kb(),
        parse_mode="Markdown"
    )


# ======================================================
#           Callback — choosing of the period
# ======================================================

@router.callback_query(F.data.startswith("stats:"))
async def stats_period(callback: types.CallbackQuery):
    period = callback.data.split(":")[1]


    async with async_session() as session:
       result = await session.execute(
           select(UserSettings).where(UserSettings.user_id == callback.from_user.id)
       )
       settings = result.scalar()
       currency = settings.currency if settings else "$"

    # Вернуться в меню
    if period == "back":
        return await callback.message.edit_text(
            "📊 *Выберите период:*",
            reply_markup=stats_menu_kb(),
            parse_mode="Markdown"
        )

    user_id = callback.from_user.id

    expenses, start, now = await get_expenses_by_period(user_id, period)

    if not expenses:
        return await callback.message.edit_text(
            "Нет данных за выбранный период.",
            reply_markup=back_kb()
        )

    total = sum(e.amount for e in expenses)
    avg = total / len(expenses)

    text = (
        f"📅 *Период:* `{start.date()} — {now.date()}`\n"
        f"💰 *Сумма:* {total:.2f}{currency}\n"
        f"🧾 *Операций:* {len(expenses)}\n"
        f"➗ *Средний расход:* {avg:.2f}{currency}\n\n"
        f"{render_category_stats(expenses, currency)}\n\n"
        f"{render_daily_dynamics(expenses, currency)}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_kb()
    )

    await callback.answer()
