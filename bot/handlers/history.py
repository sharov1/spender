from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy import select
from db.models import async_session, Expense
from bot.i18n import t
from bot.handlers.settings import get_user_settings


router = Router()


# =========================
#         FSM
# =========================

class ExpenseEditStates(StatesGroup):
    waiting_for_new_amount = State()



# =========================

def expense_actions_kb(exp_id: int, lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "edit_amount"), callback_data=f"exp_edit:{exp_id}")],
            [InlineKeyboardButton(text=t(lang, "delete"), callback_data=f"exp_del:{exp_id}")],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="history_back")],
        ]
    )


def history_keyboard(expenses, currency: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{e.category}: {e.amount:.2f}{currency}",
                    callback_data=f"exp:{e.id}"
                )
            ]
            for e in expenses
        ]
    )


# =========================
#      /history
# =========================

@router.message(Command("history"))
async def history_list(message: types.Message):
    user_id = message.from_user.id
    settings = await get_user_settings(user_id)
    lang = settings.language

    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == user_id)
            .order_by(Expense.id.desc())
            .limit(10)
        )
        expenses = result.scalars().all()

    if not expenses:
        return await message.answer(t(lang, "no_expenses"))

    await message.answer(
        t(lang, "history_title"),
        reply_markup=history_keyboard(expenses, settings.currency)
    )


# =========================
#  View of exact expense
# =========================

@router.callback_query(F.data.startswith("exp:"))
async def expense_actions(callback: types.CallbackQuery, state: FSMContext):
    exp_id = int(callback.data.split(":")[1])
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)

    if not expense:
        return await callback.answer(t(lang, "expense_not_found_alert"), show_alert=True)

    text = (
        f"{t(lang, 'expense_category', category=expense.category)}\n"
        f"{t(lang, 'expense_amount', amount=expense.amount, currency=settings.currency)}\n"
        f"{t(lang, 'expense_id', id=expense.id)}"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=expense_actions_kb(exp_id, lang)
    )
    await callback.answer()


# =========================
#     Deleting
# =========================

@router.callback_query(F.data.startswith("exp_del:"))
async def delete_expense(callback: types.CallbackQuery):
    exp_id = int(callback.data.split(":")[1])
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)
        if expense:
            await session.delete(expense)
            await session.commit()

    await callback.answer(t(lang, "deleted"))
    await callback.message.edit_text(t(lang, "expense_deleted"))


# =========================
#     Changing the summa
# =========================

@router.callback_query(F.data.startswith("exp_edit:"))
async def edit_expense(callback: types.CallbackQuery, state: FSMContext):
    exp_id = int(callback.data.split(":")[1])
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    await state.update_data(exp_id=exp_id)

    await callback.message.edit_text(
        t(lang, "enter_new_amount"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=t(lang, "back"), callback_data="history_back")]]
        )
    )

    await state.set_state(ExpenseEditStates.waiting_for_new_amount)
    await callback.answer()


@router.message(ExpenseEditStates.waiting_for_new_amount)
async def save_new_amount(message: types.Message, state: FSMContext):
    text = message.text.strip()
    settings = await get_user_settings(message.from_user.id)
    lang = settings.language

    # проверяем что число
    if not text.replace(".", "", 1).isdigit():
        return await message.answer(t(lang, "enter_correct_number_short"))

    new_amount = float(text)
    data = await state.get_data()
    exp_id = data["exp_id"]

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)

        if not expense:
            await state.clear()
            return await message.answer(t(lang, "expense_not_found"))

        expense.amount = new_amount
        await session.commit()

    await state.clear()
    await message.answer(t(lang, "amount_updated", amount=new_amount))


# =========================
#       BACK button
# =========================

@router.callback_query(F.data == "history_back")
async def history_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    lang = settings.language

    # downloading the last 10 expenses
    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == user_id)
            .order_by(Expense.id.desc())
            .limit(10)
        )
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.edit_text(t(lang, "no_expenses"))
        return await callback.answer()

    # Getting back the menuu of the last expenses
    await callback.message.edit_text(
        t(lang, "history_title"),
        reply_markup=history_keyboard(expenses, settings.currency)
    )

    await callback.answer()
