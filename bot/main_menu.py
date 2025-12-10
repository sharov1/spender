from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить расход")],
        [KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📘 История")],
        [KeyboardButton(text="⚙️ Настройки")],
    ],
    resize_keyboard=True
)
