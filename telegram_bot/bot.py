from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from django.conf import settings
from .handlers import router

async def start_bot():
    bot = Bot(
        token=settings.TG_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)