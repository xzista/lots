from aiogram import Router, types, F
from aiogram.filters import CommandStart
from .services import handle_start, handle_message, handle_admin_reply

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await handle_start(message)


@router.message(F.text & ~F.reply_to_message)
async def user_message(message: types.Message):
    await handle_message(message)


@router.message(F.reply_to_message)
async def admin_reply(message: types.Message):
    await handle_admin_reply(message)
