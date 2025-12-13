from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.handlers.settings import get_user_settings
from bot.i18n import t
from db.models import async_session, Expense   
from db.models import User                   

router = Router()


# ============ FSM STATES ============
class ExpenseStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_amount = State()



# ============ KEYBOARDS ============

async def categories_keyboard(user_id: int):
    settings = await get_user_settings(user_id)
    lang = settings.language
    cats = settings.categories.split(",")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
            for cat in cats
        ] + [
            [InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")]
        ]
    )


async def cancel_keyboard(user_id: int):
    settings = await get_user_settings(user_id)
    lang = settings.language
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "cancel"), callback_data="cancel")]
        ]
    )


# ============ HANDLERS ============

@router.message(Command("add"))
async def add_expense(message: types.Message, state: FSMContext):
    settings = await get_user_settings(message.from_user.id)
    lang = settings.language
    keyboard = await categories_keyboard(message.from_user.id)

    await message.answer(
        t(lang, "choose_category"),
        reply_markup=keyboard
    )

    await state.set_state(ExpenseStates.waiting_for_category)


@router.callback_query(F.data.startswith("cat:") & ~F.data.endswith("add"))
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    """
    User has been choosen the category → saving that in FSM → waiting for the summa
    """
    category = callback.data.split(":")[1]
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    await state.update_data(category=category)

    await callback.message.edit_text(
        f"{t(lang, 'category')}: *{category}*\n{t(lang, 'enter_amount')}",
        parse_mode="Markdown",
        reply_markup=await cancel_keyboard(callback.from_user.id)
    )
    await state.set_state(ExpenseStates.waiting_for_amount)
    await callback.answer()


@router.message(ExpenseStates.waiting_for_amount)
async def enter_amount(message: types.Message, state: FSMContext):
    """
    Step two: summa has been collected → saving in to db
    """
    text = message.text.strip()
    settings = await get_user_settings(message.from_user.id)
    lang = settings.language

    # Checking of the wroted number
    if not text.replace(".", "", 1).isdigit():
        return await message.answer(
            t(lang, "enter_correct_number"),
            reply_markup=await cancel_keyboard(message.from_user.id)
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
        t(lang, "expense_added", category=category, amount=amount),
        parse_mode="Markdown"
    )


# ============ CANCEL ============

@router.callback_query(F.data == "cancel")
async def cancel(callback: types.CallbackQuery, state: FSMContext):
    """
    Отмена на любом шаге
    """
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language
    await state.clear()
    await callback.message.edit_text(t(lang, "operation_cancelled"))
    await callback.answer()
