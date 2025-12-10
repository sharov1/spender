from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy import select
from db.models import async_session, Expense


router = Router()


# =========================
#      FSM СТАНЫ
# =========================

class ExpenseEditStates(StatesGroup):
    waiting_for_new_amount = State()


# =========================
#   ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================

def expense_actions_kb(exp_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить сумму", callback_data=f"exp_edit:{exp_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"exp_del:{exp_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="history_back")],
        ]
    )


def history_keyboard(expenses):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{e.category}: {e.amount}",
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

    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == user_id)
            .order_by(Expense.id.desc())
            .limit(10)
        )
        expenses = result.scalars().all()

    if not expenses:
        return await message.answer("У тебя пока нет записанных расходов.")

    await message.answer(
        "Последние расходы:",
        reply_markup=history_keyboard(expenses)
    )


# =========================
#  Просмотр конкретного расхода
# =========================

@router.callback_query(F.data.startswith("exp:"))
async def expense_actions(callback: types.CallbackQuery, state: FSMContext):
    exp_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)

    if not expense:
        return await callback.answer("Запись не найдена", show_alert=True)

    text = (
        f"📘 <b>Категория:</b> {expense.category}\n"
        f"💵 <b>Сумма:</b> {expense.amount}\n"
        f"🆔 <b>ID:</b> {expense.id}"
    )

    await callback.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=expense_actions_kb(exp_id)
    )
    await callback.answer()


# =========================
#     УДАЛЕНИЕ
# =========================

@router.callback_query(F.data.startswith("exp_del:"))
async def delete_expense(callback: types.CallbackQuery):
    exp_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)
        if expense:
            await session.delete(expense)
            await session.commit()

    await callback.answer("Удалено!")
    await callback.message.edit_text("🗑 Запись удалена.")


# =========================
#     ИЗМЕНЕНИЕ СУММЫ
# =========================

@router.callback_query(F.data.startswith("exp_edit:"))
async def edit_expense(callback: types.CallbackQuery, state: FSMContext):
    exp_id = int(callback.data.split(":")[1])

    await state.update_data(exp_id=exp_id)

    await callback.message.edit_text(
        "Введите новую сумму:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="⬅️ Отмена", callback_data="history_back")]]
        )
    )

    await state.set_state(ExpenseEditStates.waiting_for_new_amount)
    await callback.answer()


@router.message(ExpenseEditStates.waiting_for_new_amount)
async def save_new_amount(message: types.Message, state: FSMContext):
    text = message.text.strip()

    # проверяем что число
    if not text.replace(".", "", 1).isdigit():
        return await message.answer("Введите корректное число!")

    new_amount = float(text)
    data = await state.get_data()
    exp_id = data["exp_id"]

    async with async_session() as session:
        expense = await session.get(Expense, exp_id)

        if not expense:
            await state.clear()
            return await message.answer("Ошибка: запись не найдена.")

        expense.amount = new_amount
        await session.commit()

    await state.clear()
    await message.answer(f"✔ Сумма обновлена: {new_amount}")


# =========================
#       КНОПКА НАЗАД
# =========================

@router.callback_query(F.data == "history_back")
async def history_back(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    # Загружаем последние 10 расходов
    async with async_session() as session:
        result = await session.execute(
            select(Expense)
            .where(Expense.user_id == user_id)
            .order_by(Expense.id.desc())
            .limit(10)
        )
        expenses = result.scalars().all()

    if not expenses:
        await callback.message.edit_text("У тебя пока нет записанных расходов.")
        return await callback.answer()

    # Возвращаем меню последних трат
    await callback.message.edit_text(
        "Последние расходы:",
        reply_markup=history_keyboard(expenses)
    )

    await callback.answer()
