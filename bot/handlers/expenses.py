from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.handlers.settings import get_user_settings
from db.models import async_session, Expense   
from db.models import User                   

router = Router()


# ============ FSM STATES ============
class ExpenseStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()


#CATEGORIES = ["Food", "Transport", "Coffee", "Gifts", "Other"] ----------- старый список категорий


# ============ KEYBOARDS ============

async def categories_keyboard(user_id: int):
    settings = await get_user_settings(user_id)
    cats = settings.categories.split(",")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
            for cat in cats
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
    keyboard = await categories_keyboard(message.from_user.id)

    await message.answer(
        "Choose the category of the expense:",
        reply_markup=keyboard
    )

    await state.set_state(ExpenseStates.waiting_for_category)


@router.callback_query(F.data.startswith("cat:") & ~F.data.endswith("add"))
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    """
    User has been choosen the category → saving that in FSM → waiting for the summa
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
    Step two: summa has been collected → saving in to db
    """
    text = message.text.strip()

    # Checking of the wroted number
    if not text.replace(".", "", 1).isdigit():
        return await message.answer(
            "Введите корректное число!",
            reply_markup=cancel_keyboard()
        )

    amount = float(text)

    # Getting data from FSM
    data = await state.get_data()
    category = data["category"]

    # Saving in to db
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
