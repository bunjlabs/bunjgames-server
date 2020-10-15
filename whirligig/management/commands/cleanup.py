import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from whirligig.models import Game


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        expired_games = Game.objects.filter(expired__lt=timezone.now())
        for game in expired_games.iterator():
            print(game.token)
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token), ignore_errors=True)
        expired_games.delete()
