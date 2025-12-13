from aiogram import Router, types, html
from aiogram.filters import CommandStart
from db.models import async_session, User
from bot.main_menu import main_menu
from bot.i18n import t
from bot.handlers.settings import get_user_settings

router = Router()

async def get_or_create_user(telegram_id, username, firstname, lastname):
    async with async_session() as session:
        user = await session.get(User, telegram_id)
        if user:
            return user

        user = User(
            telegram_id=telegram_id,
            username=username,
            firstname=firstname or "",
            lastname=lastname or "",
            is_active=True
        )
        session.add(user)
        await session.commit()
        return user


@router.message(CommandStart())
async def command_start(message: types.Message):
    tg = message.from_user

    await get_or_create_user(
        telegram_id=tg.id,
        username=tg.username,
        firstname=tg.first_name,
        lastname=tg.last_name
    )


    settings = await get_user_settings(tg.id)
    lang = settings.language

    await message.answer(
        t(lang, "start", name=tg.first_name or "друг"),
        reply_markup=main_menu(lang)
    )




    #await message.answer(f"Hello {html.bold(tg.full_name)}, I'm your bot!") - old welcome

    # menu displaying
    #await message.answer(
    #    f"Привет, {html.bold(tg.first_name or 'друг')}! 👋\n\n"
    #    "Я бот учёта расходов. Выберите действие:",
    #    reply_markup=main_menu
    #)
