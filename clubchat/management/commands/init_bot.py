from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from telegram.ext import Updater


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        updater = Updater(token=settings.TELEGRAM_BOT_API_KEY)
        print(updater.bot.get_me())
        response = updater.bot.set_webhook(
            url=f'https://217.150.72.37:8443/clubchat/telegram/{settings.CLUBCHAT_TELEGRAM_BOT_TOKEN}'
        )
