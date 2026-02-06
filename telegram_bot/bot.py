from aiogram import Bot, Dispatcher
from django.conf import settings
from .handlers import router

bot = Bot(settings.TG_BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def start_bot():
    await dp.start_polling(bot)