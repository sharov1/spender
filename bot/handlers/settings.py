from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select
from db.models import async_session, UserSettings, Expense
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from bot.i18n import t

# FSM for categories adding
class CategoryStates(StatesGroup):
    waiting_for_new_category = State()


router = Router()

CURRENCIES = ["Br", "$", "€", "₾", "£", "₽"]


# ---------------------
# 📂 Category keyboards
# ---------------------

def categories_menu(categories: list, lang: str):
    """Categories menu"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ {c}", callback_data=f"cat_del:{c}")] for c in categories
        ] + [
            [InlineKeyboardButton(text=t(lang, "add_category"), callback_data="cat:add")],
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="settings:main")]
        ]
    )


# ---------------------
# 🔧 Settings buttons
# ---------------------

def currency_keyboard(lang="ru"):
    """Currency menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cur, callback_data=f"currency:{cur}")]
            for cur in CURRENCIES
        ] + [
            [InlineKeyboardButton(text=t(lang, "back"), callback_data="settings:main")]
        ]
    )


def settings_menu(lang="ru"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "currency"), callback_data="settings:currency"),
                InlineKeyboardButton(text=t(lang, "categories"), callback_data="settings:categories"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "limit"), callback_data="settings:limit"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "notifications"), callback_data="settings:notifications"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "language"), callback_data="settings:language")
            ],
            [
                InlineKeyboardButton(text=t(lang, "clear_expenses"), callback_data="settings:clear_expenses"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "back"), callback_data="settings:back"),
            ],
        ]
    )


# ---------------------
# 📌 Getting/creating settings
# ---------------------

async def get_user_settings(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar()

        if settings:
            return settings

        # Creating default settings
        settings = UserSettings(
            user_id=user_id,
            currency="$",
            categories="Food,Transport,Coffee,Gifts,Other",
            limit=None,
            notifications=True,
            language="en"
        )
        session.add(settings)
        await session.commit()
        return settings


# ---------------------
# 📂 Category handlers
# ---------------------

async def add_category(user_id: int, new_cat: str):
    async with async_session() as session:
        result = await session.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        settings = result.scalar()
        cats = settings.categories.split(",")

        if new_cat not in cats:
            cats.append(new_cat)
            settings.categories = ",".join(cats)
            session.add(settings)
            await session.commit()


async def delete_category(user_id: int, cat: str):
    async with async_session() as session:
        result = await session.execute(select(UserSettings).where(UserSettings.user_id == user_id))
        settings = result.scalar()
        cats = settings.categories.split(",")

        if cat in cats:
            cats.remove(cat)
            settings.categories = ",".join(cats)
            session.add(settings)
            await session.commit()


# ---------------------
# ⚙️ /settings
# ---------------------

@router.message(Command("settings"))
async def settings_cmd(message: types.Message):
    settings = await get_user_settings(message.from_user.id)

    await message.answer(
        t(settings.language, "settings_title"),
        parse_mode="HTML",
        reply_markup=settings_menu(settings.language)
    )


# ---------------------
# ⚙️ Processing settings menu
# ---------------------

@router.callback_query(F.data.startswith("settings:"))
async def settings_callback(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    if action == "back":
        return await callback.message.edit_text(t(lang, "back"))

    if action == "main":
        return await callback.message.edit_text(
            t(lang, "settings_title"),
            parse_mode="HTML",
            reply_markup=settings_menu(lang)
        )

    if action == "currency":
        return await callback.message.edit_text(
            t(lang, "choose_currency"),
            parse_mode="HTML",
            reply_markup=currency_keyboard(lang)
        )

    if action == "categories":
        cats = settings.categories.split(",")
        return await callback.message.edit_text(
            t(lang, "your_categories"),
            parse_mode="HTML",
            reply_markup=categories_menu(cats, lang)
        )

    if action == "limit":
        return await callback.message.edit_text(
            t(lang, "limit_coming_soon"),
            reply_markup=settings_menu(lang)
        )

    if action == "clear_expenses":
        return await callback.message.edit_text(
            t(lang, "clear_expenses_confirm"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=t(lang, "delete_all"), callback_data="confirm_clear_expenses")],
                    [InlineKeyboardButton(text=t(lang, "back"), callback_data="settings:main")]
                ]
            )
        )

    if action == "language":
        return await callback.message.edit_text(
            t(lang, "choose_language"),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
                    [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
                    [InlineKeyboardButton(text=t(lang, "back"), callback_data="settings:main")],
                ]
            )
        )

    if action == "notifications":
        settings.notifications = not settings.notifications

        async with async_session() as session:
            session.add(settings)
            await session.commit()

        status = t(lang, "notifications_on") if settings.notifications else t(lang, "notifications_off")

        return await callback.message.edit_text(
            status,
            parse_mode="HTML",
            reply_markup=settings_menu(lang)
        )

    await callback.answer()


# ---------------------
# 💱 Currency change
# ---------------------

@router.callback_query(F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery):
    symbol = callback.data.split(":")[1]

    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language
    settings.currency = symbol

    async with async_session() as session:
        session.add(settings)
        await session.commit()

    await callback.message.edit_text(
        f"{t(lang, 'currency')}: <b>{symbol}</b>",
        parse_mode="HTML",
        reply_markup=settings_menu(lang)
    )
    await callback.answer()


# ---------------------
# 💱 Categories add/del
# ---------------------

@router.callback_query(F.data.startswith("cat_del:"))
async def delete_cat_cb(callback: CallbackQuery):
    cat = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await delete_category(user_id, cat)
    settings = await get_user_settings(user_id)
    lang = settings.language
    cats = settings.categories.split(",")

    await callback.message.edit_text(
        t(lang, "categories"),
        parse_mode="HTML",
        reply_markup=categories_menu(cats, lang)
    )
    await callback.answer()


@router.callback_query(F.data == "cat:add")
async def add_cat_start(callback: CallbackQuery, state: FSMContext):
    settings = await get_user_settings(callback.from_user.id)
    lang = settings.language

    await callback.message.edit_text(t(lang, "enter_new_category"))
    await state.set_state(CategoryStates.waiting_for_new_category)
    await callback.answer()


@router.message(CategoryStates.waiting_for_new_category)
async def add_cat_text(message: types.Message, state: FSMContext):
    new_cat = message.text.strip()

    await add_category(message.from_user.id, new_cat)
    await state.clear()

    settings = await get_user_settings(message.from_user.id)
    lang = settings.language
    cats = settings.categories.split(",")

    await message.answer(
        t(lang, "category_added", new_cat=new_cat),
        parse_mode="HTML",
        reply_markup=categories_menu(cats, lang),
    )


@router.callback_query(F.data == "confirm_clear_expenses")
async def clear_all_expenses(callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = await get_user_settings(user_id)
    lang = settings.language

    async with async_session() as session:
        await session.execute(
            Expense.__table__.delete().where(Expense.user_id == user_id)
        )
        await session.commit()

    await callback.message.edit_text(
        t(lang, "all_expenses_deleted"),
        reply_markup=settings_menu(lang)
    )
    await callback.answer()


# ---------------
# 🌐 Language change
# ---------------

@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    settings = await get_user_settings(callback.from_user.id)
    settings.language = lang

    async with async_session() as session:
        session.add(settings)
        await session.commit()

    await callback.message.edit_text(
        f"{t(lang, 'language')}: {'Русский 🇷🇺' if lang=='ru' else 'English 🇬🇧'}",
        reply_markup=settings_menu(lang)
    )
    
    # Обновляем главное меню с новым языком
    from bot.main_menu import main_menu
    await callback.message.answer(
        f"✅ {t(lang, 'language_changed')}",
        reply_markup=main_menu(lang)
    )
    
    await callback.answer()
