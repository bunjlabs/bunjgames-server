import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist

from jeopardy.models import Game
from jeopardy.serializers import GameSerializer

logger = logging.getLogger(__name__)


class JeopardyConsumer(WebsocketConsumer):
    token = None
    room_name = None

    routes = dict(
        next_state=lambda game, from_state: game.next_state(from_state),
        choose_question=lambda game, question_id: game.choose_question(question_id),
        end_question=lambda game, player_id, balance_diff: game.end_question(player_id, balance_diff),
        skip_question=lambda game: game.skip_question(),
        button_click=lambda game, player_id: game.button_click(player_id),
        final_bet=lambda game, player_id, bet: game.final_bet(player_id, bet),
        final_answer=lambda game, player_id, answer: game.final_answer(player_id, answer),
        set_balance=lambda game, balance_list: game.set_balance(balance_list),
        set_round=lambda game, round: game.set_round(round),
    )

    def connect(self):
        self.token = self.scope['url_route']['kwargs']['token']
        self.room_name = 'jeopardy_%s' % self.token

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
