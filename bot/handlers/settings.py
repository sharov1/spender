from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select

from db.models import async_session, UserSettings

router = Router()

CURRENCIES = ["Br", "$", "€", "₾", "£", "₽"]



# ---------------------
# 📂 Category keyboards
# ---------------------

def categories_menu(categories: list):
    """Categories menu"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"❌ {c}", callback_data=f"cat_del:{c}")] for c in categories
        ] + [
            [InlineKeyboardButton(text="➕ Добавить категорию", callback_data="cat:add")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:main")]
        ]
    )



# ---------------------
# 🔧 Settings buttons
# ---------------------

def currency_keyboard():
    """Currency menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=cur, callback_data=f"currency:{cur}")]
            for cur in CURRENCIES
        ] + [
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:main")]
        ]
    )


def settings_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💱 Валюта", callback_data="settings:currency"),
                InlineKeyboardButton(text="📂 Категории", callback_data="settings:categories"),
            ],
            [
                InlineKeyboardButton(text="⚠️ Лимит расходов", callback_data="settings:limit"),
            ],
            [
                InlineKeyboardButton(text="🔕 Уведомления", callback_data="settings:notifications"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:back"),
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

        # Creating the default settings
        settings = UserSettings(
            user_id=user_id,
            currency="$",
            categories="Food,Transport,Coffee,Gifts,Other",
            limit=None,
            notifications=True
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
    await message.answer(
        "⚙️ <b>Настройки бота</b>\nВыберите параметр:",
        parse_mode="HTML",
        reply_markup=settings_menu()
    )


# ---------------------
# ⚙️ Processing of settings menu
# ---------------------

@router.callback_query(F.data.startswith("settings:"))
async def settings_callback(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "back":
        return await callback.message.edit_text(
            "Главное меню закрыто 👌"
        )

    if action == "main":
        return await callback.message.edit_text(
            "⚙️ <b>Настройки бота</b>",
            parse_mode="HTML",
            reply_markup=settings_menu()
        )

    if action == "currency":
        return await callback.message.edit_text(
            "💱 Выберите валюту:",
            parse_mode="HTML",
            reply_markup=currency_keyboard()
        )

    if action == "categories":
        settings = await get_user_settings(callback.from_user.id)
        cats = settings.categories.split(",")
        return await callback.message.edit_text(
            "📂 <b>Ваши категории</b>\nНажмите на категорию, чтобы удалить.",
            parse_mode="HTML",
            reply_markup=categories_menu(cats)
    )

    if action == "limit":
        return await callback.message.edit_text(
            "⚠️ Лимит расходов скоро будет реализован 👍",
            reply_markup=settings_menu()
        )

    if action == "notifications":
        settings = await get_user_settings(callback.from_user.id)
        settings.notifications = not settings.notifications

        async with async_session() as session:
            session.add(settings)
            await session.commit()

        status = "🔔 Включены" if settings.notifications else "🔕 Выключены"

        return await callback.message.edit_text(
            f"Уведомления: <b>{status}</b>",
            parse_mode="HTML",
            reply_markup=settings_menu()
        )

    await callback.answer()


# ---------------------
# 💱 Choosing currency
# ---------------------

@router.callback_query(F.data.startswith("currency:"))
async def choose_currency(callback: CallbackQuery):
    """Changing currency by user"""
    symbol = callback.data.split(":")[1]

    settings = await get_user_settings(callback.from_user.id)
    settings.currency = symbol

    async with async_session() as session:
        session.add(settings)
        await session.commit()

    await callback.message.edit_text(
        f"💱 Валюта обновлена на <b>{symbol}</b>!",
        parse_mode="HTML",
        reply_markup=settings_menu()
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
    cats = settings.categories.split(",")

    await callback.message.edit_text(
        "📂 <b>Ваши категории</b>\nКатегория удалена.",
        parse_mode="HTML",
        reply_markup=categories_menu(cats)
    )
    await callback.answer()


@router.callback_query(F.data == "cat:add")
async def add_cat_start(callback: CallbackQuery):
    await callback.message.edit_text(
        "Введите название новой категории:",
    )
    await callback.answer()

    
    router.category_add_mode = callback.from_user.id


@router.message()
async def add_cat_text(message: types.Message):
    
    if getattr(router, "category_add_mode", None) != message.from_user.id:
        return

    router.category_add_mode = None  # Сбрасываем режим

    new_cat = message.text.strip()
    await add_category(message.from_user.id, new_cat)

    settings = await get_user_settings(message.from_user.id)
    cats = settings.categories.split(",")

    await message.answer(
        f"Категория <b>{new_cat}</b> добавлена!",
        parse_mode="HTML",
        reply_markup=categories_menu(cats)
    )
