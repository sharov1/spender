import asyncio
import logging
import sys

from aiogram import Bot, html, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import settings
from bot.handlers import start_router, expenses_router, echo_router, stats_router, settings_router


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    # Routers connection
    dp.include_router(start_router)
    dp.include_router(expenses_router)
    dp.include_router(stats_router)
    dp.include_router(settings_router)
    dp.include_router(echo_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
