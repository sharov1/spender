from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.i18n import t 

def main_menu(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "menu_add_expense"))],
            [KeyboardButton(text=t(lang, "menu_stats"))],
            [KeyboardButton(text=t(lang, "menu_history"))],
            [KeyboardButton(text=t(lang, "menu_settings"))],
        ],
        resize_keyboard=True
    )
