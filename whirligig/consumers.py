import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from whirligig.models import Game
from whirligig.serializers import GameSerializer

logger = logging.getLogger(__name__)


class WhirligigConsumer(WebsocketConsumer):
    token = None
    room_name = None

    routes = dict(
        next_state=lambda game, from_state: game.next_state(from_state),
        change_score=lambda game, connoisseurs_score, viewers_score: game.change_score(connoisseurs_score,
                                                                                       viewers_score),
        change_timer=lambda game, paused: game.change_timer(paused),
        answer_correct=lambda game, is_correct: game.answer_correct(is_correct)
    )

    def connect(self):
        self.token = self.scope['url_route']['kwargs']['token']
        self.room_name = 'whirligig_%s' % self.token

        try:
            game = Game.objects.get(token=self.token)
            async_to_sync(self.channel_layer.group_add)(
                self.room_name,
                self.channel_name
            )
            self.accept()
            self.send(text_data=json.dumps({
                'type': 'game',
                'message': GameSerializer().to_representation(game)
            }))
        except ObjectDoesNotExist:
            logger.debug('Bad token')
            self.close()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        game = Game.objects.get(token=self.token)

        try:
            if data['method'] == 'intercom':
                async_to_sync(self.channel_layer.group_send)(self.room_name, {
                    'type': 'intercom',
                    'message': data['message']
                })
            else:
                self.routes[data['method']](game, **data['params'])

                async_to_sync(self.channel_layer.group_send)(self.room_name, {
                    'type': 'game',
                    'message': GameSerializer().to_representation(game)
                })
        except (KeyError, TypeError, ValueError) as e:
            logger.warning('Bad request: %s' % str(e))

    def intercom(self, event):
        self.send(text_data=json.dumps(event))

    def game(self, event):
        self.send(text_data=json.dumps(event))
