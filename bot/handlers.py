from main import bot
from aiogram import Router, html, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Dispatcher

from aiogram.fsm.context import FSMContext
from db.models import async_session, User

#router = Router()

dp = Dispatcher()



async def get_or_create_user(telegram_id: int, username: str, firstname: str, lastname: str):
    async with async_session() as session:
        # Проверяем есть ли пользователь
        user = await session.get(User, telegram_id)

        if user:
            return user

        # Создаём нового
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


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    tg = message.from_user

    # регистрируем пользователя
    await get_or_create_user(
        telegram_id=tg.id,
        username=tg.username,
        firstname=tg.first_name,
        lastname=tg.last_name
    )

    await message.answer(
        f"Hello {html.bold(message.from_user.full_name)}, I'm your bot!"
    )



#router = Router()
#@router.message(F.text == "/add")
#async def start_add_expense(message: Message, state: FSMContext):
#    await state.set_state(AddExpenseState.amount)
#    await message.answer("Введите сумму расхода:")

@dp.message(F.text == "/add")
async def start_add_expense(message: Message, state: FSMContext):
    await state.set_state(AddExpenseState.amount)
    await message.answer("Введите сумму расхода:")


#@dp.message(CommandStart())
#async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
 #   await message.answer(f"Hello {html.bold(message.from_user.full_name)}, Im your bot!")

@dp.message()
async def echo_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")