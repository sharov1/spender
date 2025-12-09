from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db.models import async_session, Expense   # твоя модель расходов
from db.models import User                     # понадобится для user_id

router = Router()


# ============ FSM STATES ============
class ExpenseStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()


CATEGORIES = ["Food", "Transport", "Coffee", "Gifts", "Other"]


# ============ KEYBOARDS ============

def categories_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
            for cat in CATEGORIES
        ] + [
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="cancel")]
        ]
    )


def cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Отмена", callback_data="cancel")]
        ]
    )


# ============ HANDLERS ============

@router.message(Command("add"))
async def add_expense(message: types.Message, state: FSMContext):
    """
    Первый шаг: показываем категории
    """
    await message.answer(
        "Выбери категорию расхода:",
        reply_markup=categories_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_for_category)


@router.callback_query(F.data.startswith("cat"))
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    """
    Пользователь выбрал категорию → сохраняем её в FSM → ждём сумму
    """
    category = callback.data.split(":")[1]

    await state.update_data(category=category)

    await callback.message.edit_text(
        f"Категория: *{category}*\nВведите сумму расхода:",
        parse_mode="Markdown",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(ExpenseStates.waiting_for_amount)
    await callback.answer()


@router.message(ExpenseStates.waiting_for_amount)
async def enter_amount(message: types.Message, state: FSMContext):
    """
    Второй шаг: введена сумма → сохраняем в БД
    """
    text = message.text.strip()

    # Проверка суммы
    if not text.replace(".", "", 1).isdigit():
        return await message.answer(
            "Введите корректное число!",
            reply_markup=cancel_keyboard()
        )

    amount = float(text)

    # Достаём данные из FSM
    data = await state.get_data()
    category = data["category"]

    # Сохраняем в БД
    async with async_session() as session:
        expense = Expense(
            user_id=message.from_user.id,
            category=category,
            amount=amount
        )
        session.add(expense)
        await session.commit()

    await state.clear()

    await message.answer(
        f"🟢 *Расход добавлен!*\n\n"
        f"Категория: *{category}*\n"
        f"Сумма: *{amount}*",
        parse_mode="Markdown"
    )


# ============ CANCEL ============

@router.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    """
    Отмена на любом шаге
    """
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена.")
    await callback.answer()
