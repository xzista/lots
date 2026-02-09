from django.core.management.base import BaseCommand
import asyncio
from telegram_bot.bot import start_bot


class Command(BaseCommand):
    help = "Run telegram bot"

    def handle(self, *args, **kwargs):
        asyncio.run(start_bot())