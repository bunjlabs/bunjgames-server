import os
import shutil

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unzip
from whirligig.models import Game
from whirligig.serializers import GameSerializer


class CreateGameAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        game = Game.new()

        data = request.data['game']
        path = default_storage.save(os.path.join('whirligig', game.token, 'game'), ContentFile(data.read()))
        file = os.path.join(settings.MEDIA_ROOT, path)
        try:
            unzip(file, os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token))
        finally:
            os.remove(file)

        try:
            game.parse(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token, 'content.xml'))
            os.remove(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token, 'content.xml'))
        except Exception as e:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token), ignore_errors=True)
            raise e

        if not os.listdir(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token)):
            os.rmdir(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token))

        return Response(GameSerializer().to_representation(game))
