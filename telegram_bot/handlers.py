from aiogram import Router, types, F
from aiogram.filters import CommandStart
from .services import handle_start, handle_message, handle_admin_reply, handle_close_topic

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message):
    await handle_start(message)


@router.message(F.text & (F.chat.type == "private"))
async def user_message(message: types.Message):
    await handle_message(message)


@router.message(F.reply_to_message & (F.chat.type == "supergroup"))
async def admin_reply(message: types.Message):
    await handle_admin_reply(message)

@router.callback_query(F.data.startswith("close_topic_"))
async def close_callback(callback: types.CallbackQuery):
    await handle_close_topic(callback)