from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(F.text == "/add")
async def start_add_expense(message: Message, state: FSMContext):
    await state.set_state(AddExpenseState.amount)
    await message.answer("Введите сумму расхода:")
