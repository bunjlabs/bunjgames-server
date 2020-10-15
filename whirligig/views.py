import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from common.utils import unzip
from common.views import TokenContextMixin
from whirligig.models import Game, BadStateException
from whirligig.serializers import GameSerializer


class GameAPI(TokenContextMixin, generics.RetrieveAPIView):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

    def get_object(self):
        return get_object_or_404(self.get_queryset(), token=self.token)


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

        game.parse(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token, 'content.xml'))
        os.remove(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token, 'content.xml'))

        if not os.listdir(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token)):
            os.rmdir(os.path.join(settings.MEDIA_ROOT_WHIRLIGIG, game.token))

        return Response(GameSerializer().to_representation(game))


class NextStateAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        try:
            game = get_object_or_404(Game.objects.all(), token=request.data.get('token'))
            game.next_state()
            return Response(GameSerializer().to_representation(game))
        except BadStateException:
            return Response(status=400)


class ChangeScoreAPI(APIView):
    serializer_class = GameSerializer

    @transaction.atomic()
    def post(self, request):
        game = get_object_or_404(Game.objects.all(), token=request.data.get('token'))
        game.change_score(request.data.get('connoisseurs_score'), request.data.get('viewers_score'))
        return Response(GameSerializer().to_representation(game))
