from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from bot.main_menu import main_menu
from bot.handlers.expenses import add_expense
from bot.handlers.settings import settings_cmd
from bot.handlers.stats import stats_cmd
from bot.handlers.history import history_list

router = Router()


@router.message(F.text == "➕ Добавить расход")
async def menu_add_expense(message: types.Message, state: FSMContext):
    await add_expense(message, state)

@router.message(F.text == "📊 Статистика")
async def menu_stats(message: types.Message):
    await stats_cmd(message)

@router.message(F.text == "📘 История")
async def menu_history (message: types.Message):
    await history_list(message)

@router.message(F.text == "⚙️ Настройки")
async def menu_settings(message: types.Message):
    await settings_cmd(message)
