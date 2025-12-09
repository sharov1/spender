from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select

from db.models import async_session, UserSettings

router = Router()

CURRENCIES = ["Br", "$", "€", "₾", "£", "₽"]



# ---------------------
# 🔧 Settings buttons
# ---------------------


def currency_keyboard():
    """Меню выбора валюты."""
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


def currency_menu():
    currencies = ["₽", "$", "€", "£"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=c, callback_data=f"currency:{c}")]
            for c in currencies
        ] + [[InlineKeyboardButton(text="⬅️ Назад", callback_data="settings:main")]]
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
        return await callback.message.edit_text(
            f"📂 <b>Ваши категории:</b>\n{settings.categories}\n\n"
            f"Пока редактирование категории реализуем позже 🙂",
            parse_mode="HTML",
            reply_markup=settings_menu()
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
    """Изменение валюты пользователем."""
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


