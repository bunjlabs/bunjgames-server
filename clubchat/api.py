import logging

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import Updater

from django.conf import settings

from clubchat.commands import Command, TelegramCommandHandler
from common.utils import BadFormatException, BadStateException

logger = logging.getLogger(__name__)


@csrf_exempt
def on_telegram_message_callback(request, token):
    updater = Updater(token=settings.TELEGRAM_BOT_API_KEY)
    update = Update.de_json(request.json(), updater.bot)

    if token != settings.CLUBCHAT_TELEGRAM_BOT_TOKEN:
        updater.bot.send_message(chat_id=update.message.chat.id, text='Invalid token')
        return HttpResponseForbidden()

    chat_id = update.message.chat.id if update.message is not None else update.callback_query.message.chat.id
    command_text = update.message.text.strip() \
        if update.message is not None and update.message.text \
        else (update.callback_query.data if update.callback_query is not None else None)

    try:
        command = Command(command_text, TelegramCommandHandler(chat_id, updater))
        command.handle()
    except (BadFormatException, BadStateException) as exception:
        updater.bot.send_message(chat_id=chat_id, text=str(exception))
    except Exception as exception:
        logger.error(str(exception))
    return HttpResponse()
