from aiogram import Router, types, html
from aiogram.filters import CommandStart
from db.models import async_session, User

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

    await message.answer(f"Hello {html.bold(tg.full_name)}, I'm your ref bot!")
