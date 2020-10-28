import logging
import os
import shutil

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unzip, BadStateException, BadFormatException
from jeopardy.models import Game, Player
from jeopardy.serializers import GameSerializer


logger = logging.getLogger(__name__)


class CreateGameAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        game = Game.new()

        data = request.data['game']
        path = default_storage.save(os.path.join('jeopardy', game.token, 'game'), ContentFile(data.read()))
        file = os.path.join(settings.MEDIA_ROOT, path)
        try:
            unzip(file, os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token))
        finally:
            os.remove(file)

        try:
            game.parse(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token, 'content.xml'))
            os.remove(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token, 'content.xml'))
        except Exception as e:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token), ignore_errors=True)
            logger.error(str(e))
            if isinstance(e, BadFormatException) or isinstance(e, BadStateException):
                raise e
            raise BadFormatException("Bad game file")

        if not os.listdir(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token)):
            os.rmdir(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token))

        return Response(GameSerializer().to_representation(game))


class RegisterPlayerAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        token, name = request.data['token'], request.data['name'].upper().strip()
        try:
            game = Game.objects.get(token=token)
        except ObjectDoesNotExist:
            raise BadStateException('Game not found')
        try:
            player = Player.objects.get(game=game, name=name)
        except ObjectDoesNotExist:
            if game.state != Game.STATE_WAITING_FOR_PLAYERS or game.players.count() >= 3:
                raise BadStateException('Game already started')
            player = Player.objects.create(game=game, name=name)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(f'jeopardy_{game.token}', {
                'type': 'game',
                'message': GameSerializer().to_representation(game)
            })
        return Response({
            'player_id': player.id,
            'game': GameSerializer().to_representation(game)
        })
