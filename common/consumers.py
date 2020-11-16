import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from common.utils import BadStateException, BadFormatException, NothingToDoException

logger = logging.getLogger(__name__)


class Consumer(WebsocketConsumer):
    token = None
    room_name = None

    @property
    def routes(self):
        raise NotImplemented()

    @property
    def game_name(self):
        raise NotImplemented()

    def get_game(self, token):
        raise NotImplemented()

    def serialize_game(self, game):
        raise NotImplemented()

    def connect(self):
        self.token = self.scope['url_route']['kwargs']['token'].upper().strip()
        self.room_name = f'{self.game_name}_{self.token}'

        try:
            game = self.get_game(self.token)
            async_to_sync(self.channel_layer.group_add)(
                self.room_name,
                self.channel_name
            )
            self.accept()
            self.send(text_data=json.dumps({
                'type': 'game',
                'message': self.serialize_game(game)
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

        game = self.get_game(self.token)

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
                    'message': self.serialize_game(game)
                })
        except NothingToDoException:
            pass
        except (BadStateException, BadFormatException, KeyError, TypeError, ValueError) as e:
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
            logger.warning('Bad request: %s' % str(e))

    def intercom(self, event):
        self.send(text_data=json.dumps(event))

    def game(self, event):
        self.send(text_data=json.dumps(event))
