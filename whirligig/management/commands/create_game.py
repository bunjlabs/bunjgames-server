from django.core.management.base import BaseCommand
from django.db import transaction

from whirligig.models import Game


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        game = Game.new()
        game.parse('content.xml')
        print(game.token)
