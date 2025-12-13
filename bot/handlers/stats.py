from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
import datetime
from db.models import async_session, Expense, UserSettings
from bot.i18n import t
from bot.handlers.settings import get_user_settings

router = Router()

# ======================================================
#                    UI BUTTONS
# ======================================================

def stats_menu_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "stats_today"), callback_data="stats:day"),
                InlineKeyboardButton(text=t(lang, "stats_week"), callback_data="stats:week")
            ],
            [
                InlineKeyboardButton(text=t(lang, "stats_month"), callback_data="stats:month"),
                InlineKeyboardButton(text=t(lang, "stats_year"), callback_data="stats:year")
            ],
        ]
    )


def back_kb(lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t(lang, "back"), callback_data="stats:back")]]
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

def render_category_stats(expenses, currency, lang: str):
    categories = {}
    for e in expenses:
        categories[e.category] = categories.get(e.category, 0) + e.amount

    if not categories:
        return t(lang, "no_data")

    max_value = max(categories.values())
    lines = [t(lang, "stats_by_categories"), ""]

    for name, value in categories.items():
        bar = bar_chart(value, max_value)
        lines.append(f"{name}: `{bar}` — *{value:.2f}{currency}*")

    return "\n".join(lines)


# ======================================================
#        Dynamic of the expenses by dates
# ======================================================

def render_daily_dynamics(expenses, currency, lang: str):
    days = {}
    for e in expenses:
        d = e.created_at.date()
        days[d] = days.get(d, 0) + e.amount

    if not days:
        return t(lang, "no_data")

    max_value = max(days.values())
    lines = [t(lang, "stats_dynamics"), ""]

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
    settings = await get_user_settings(message.from_user.id)
    lang = settings.language
    
    await message.answer(
        t(lang, "stats_choose_period"),
        reply_markup=stats_menu_kb(lang),
        parse_mode="Markdown"
    )


# ======================================================
#           Callback — choosing of the period
# ======================================================

@router.callback_query(F.data.startswith("stats:"))
async def stats_period(callback: types.CallbackQuery):
    period = callback.data.split(":")[1]
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language
    currency = settings.currency

    # Вернуться в меню
    if period == "back":
        return await callback.message.edit_text(
            t(lang, "stats_period"),
            reply_markup=stats_menu_kb(lang),
            parse_mode="Markdown"
        )

    user_id = callback.from_user.id

    expenses, start, now = await get_expenses_by_period(user_id, period)

    if not expenses:
        return await callback.message.edit_text(
            t(lang, "no_data_period"),
            reply_markup=back_kb(lang)
        )

    total = sum(e.amount for e in expenses)
    avg = total / len(expenses)

    text = (
        f"{t(lang, 'stats_period_label')} `{start.date()} — {now.date()}`\n"
        f"{t(lang, 'stats_total')} {total:.2f}{currency}\n"
        f"{t(lang, 'stats_operations')} {len(expenses)}\n"
        f"{t(lang, 'stats_avg_expense')} {avg:.2f}{currency}\n\n"
        f"{render_category_stats(expenses, currency, lang)}\n\n"
        f"{render_daily_dynamics(expenses, currency, lang)}"
    )

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=back_kb(lang)
    )

    await callback.answer()
