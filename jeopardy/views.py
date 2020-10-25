import os

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

from common.utils import unzip, BadStateException
from jeopardy.consumers import JeopardyConsumer
from jeopardy.models import Game, Player
from jeopardy.serializers import GameSerializer


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

        game.parse(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token, 'content.xml'))
        os.remove(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token, 'content.xml'))

        if not os.listdir(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token)):
            os.rmdir(os.path.join(settings.MEDIA_ROOT_JEOPARDY, game.token))

        return Response(GameSerializer().to_representation(game))


class RegisterPlayerAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        token, name = request.data['token'], request.data['name']
        game = get_object_or_404(Game, token=token)
        try:
            player = Player.objects.get(game=game, name=name)
        except ObjectDoesNotExist:
            if game.state != Game.STATE_WAITING_FOR_PLAYERS or game.players.count() >= 3:
                raise BadStateException()
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
