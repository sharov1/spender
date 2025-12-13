from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from bot.main_menu import main_menu
from bot.handlers.expenses import add_expense
from bot.handlers.settings import settings_cmd
from bot.handlers.stats import stats_cmd
from bot.handlers.history import history_list
from bot.i18n import t
from bot.handlers.settings import get_user_settings  

router = Router()


async def get_lang(user_id: int) -> str:
    """Small helper to get language quickly."""
    settings = await get_user_settings(user_id)
    return settings.language


@router.message(F.text)
async def menu_router(message: types.Message, state: FSMContext):
    settings = await get_user_settings(message.from_user.id)
    lang = settings.language
    text = message.text
    
    # Получаем все возможные тексты кнопок меню на обоих языках
    menu_texts = [
        t(lang, "menu_add_expense"),
        t(lang, "menu_stats"),
        t(lang, "menu_history"),
        t(lang, "menu_settings"),
    ]
    
    other_lang = "en" if lang == "ru" else "ru"
    menu_texts.extend([
        t(other_lang, "menu_add_expense"),
        t(other_lang, "menu_stats"),
        t(other_lang, "menu_history"),
        t(other_lang, "menu_settings"),
    ])
    
    # Если это не кнопка меню, и пользователь в FSM состоянии - пропускаем
    current_state = await state.get_state()
    if current_state is not None and text not in menu_texts:
        return  # Позволяем другим обработчикам обработать это сообщение
    
    # Если это кнопка меню и пользователь в FSM состоянии - очищаем состояние
    if current_state is not None and text in menu_texts:
        await state.clear()
    
    # Проверяем текст кнопок на текущем языке
    if text == t(lang, "menu_add_expense"):
        return await add_expense(message, state)

    if text == t(lang, "menu_stats"):
        return await stats_cmd(message)

    if text == t(lang, "menu_history"):
        return await history_list(message)

    if text == t(lang, "menu_settings"):
        return await settings_cmd(message)
    
    # Проверяем текст кнопок на другом языке (на случай, если меню еще не обновилось)
    if text == t(other_lang, "menu_add_expense"):
        return await add_expense(message, state)

    if text == t(other_lang, "menu_stats"):
        return await stats_cmd(message)

    if text == t(other_lang, "menu_history"):
        return await history_list(message)

    if text == t(other_lang, "menu_settings"):
        return await settings_cmd(message)


#text = t(lang, "add_expense")
#await message.answer(text)

