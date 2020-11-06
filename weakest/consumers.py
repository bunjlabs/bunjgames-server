from common.consumers import Consumer
from weakest.models import Game
from weakest.serializers import GameSerializer


class WeakestConsumer(Consumer):

    @property
    def routes(self):
        return dict(
            next_state=lambda game, from_state: game.next_state(from_state),
            save_bank=lambda game: game.save_bank(),
            answer_correct=lambda game, is_correct: game.answer_correct(is_correct),
            select_weakest=lambda game, player_id, weakest_id: game.select_weakest(player_id, weakest_id),
            select_final_answerer=lambda game, player_id: game.select_final_answerer(player_id),
        )

    @property
    def game_name(self):
        return 'weakest'

    def get_game(self, token):
        return Game.objects.get(token=token)

    def serialize_game(self, game):
        return GameSerializer().to_representation(game)
