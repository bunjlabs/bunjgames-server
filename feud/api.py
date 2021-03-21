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
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import BadStateException, BadFormatException
from feud.models import Game, Team
from feud.serializers import GameSerializer

logger = logging.getLogger(__name__)


class CreateGameAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        game = Game.new()

        data = request.data['game']
        path = default_storage.save(os.path.join('feud', game.token, 'game'), ContentFile(data.read()))
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
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT_FEUD, game.token), ignore_errors=True)

        return Response(GameSerializer().to_representation(game))


class RegisterTeamAPI(APIView):
    serializer_class = GameSerializer

    def post(self, request):
        token, name = request.data['token'].upper().strip(), request.data['name'].upper().strip()
        try:
            game = Game.objects.get(token=token)
        except ObjectDoesNotExist:
            raise BadStateException('Game not found')
        try:
            team = Team.objects.get(game=game, name=name)
        except ObjectDoesNotExist:
            if game.get_teams().count() >= 2:
                raise BadStateException('Game already have 2 teams')
            if game.state != Game.STATE_WAITING_FOR_TEAMS:
                raise BadStateException('Game already started')
            team = Team.objects.create(game=game, name=name)
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(f'feud_{game.token}', {
                'type': 'game',
                'message': GameSerializer().to_representation(game)
            })
        return Response({
            'team_id': team.id,
            'game': GameSerializer().to_representation(game)
        })
