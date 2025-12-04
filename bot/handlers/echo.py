from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def echo(message: Message):
    try:
        await message.send_copy(message.chat.id)
    except TypeError:
        await message.answer("Nice try!")
