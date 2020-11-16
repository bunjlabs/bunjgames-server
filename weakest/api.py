import logging
import os

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unzip, BadStateException, BadFormatException
from weakest.models import Game, Player
from weakest.serializers import GameSerializer


logger = logging.getLogger(__name__)


class CreateGameAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        game = Game.new()

        data = request.data['game']
        path = default_storage.save(os.path.join('weakest', game.token, 'game'), ContentFile(data.read()))
        file = os.path.join(settings.MEDIA_ROOT, path)

        try:
            game.parse(file)
        except (BadFormatException, BadStateException) as e:
            raise e
        except Exception as e:
            logger.error(str(e))
            raise BadFormatException("Bad game file")
        finally:
            os.remove(file)

        return Response(GameSerializer().to_representation(game))


class RegisterPlayerAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        token, name = request.data['token'].upper().strip(), request.data['name'].upper().strip()
        try:
            game = Game.objects.get(token=token)
        except ObjectDoesNotExist:
            raise BadStateException('Game not found')
        try:
            player = Player.objects.get(game=game, name=name)
        except ObjectDoesNotExist:
            if game.state != Game.STATE_WAITING_FOR_PLAYERS:
                raise BadStateException('Game already started')
            player = Player.objects.create(game=game, name=name)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(f'weakest_{game.token}', {
                'type': 'game',
                'message': GameSerializer().to_representation(game)
            })
        return Response({
            'player_id': player.id,
            'game': GameSerializer().to_representation(game)
        })
