from common.consumers import Consumer
from feud.models import Game
from feud.serializers import GameSerializer


class FeudConsumer(Consumer):

    @property
    def routes(self):
        return dict(
            next_state=lambda game, from_state: game.next_state(from_state),
            button_click=lambda game, team_id: game.button_click(team_id),
            set_answerer=lambda game, team_id: game.set_answerer(team_id),
            answer=lambda game, is_correct, answer_id: game.answer(is_correct, answer_id),
        )

    @property
    def game_name(self):
        return 'feud'

    def get_game(self, token):
        return Game.objects.get(token=token)

    def serialize_game(self, game):
        return GameSerializer().to_representation(game)
