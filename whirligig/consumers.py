from common.consumers import Consumer
from whirligig.models import Game
from whirligig.serializers import GameSerializer


class WhirligigConsumer(Consumer):

    @property
    def routes(self):
        return dict(
            next_state=lambda game, from_state: game.next_state(from_state),
            change_score=lambda game, connoisseurs_score, viewers_score: game.change_score(
                connoisseurs_score, viewers_score),
            change_timer=lambda game, paused: game.change_timer(paused),
            answer_correct=lambda game, is_correct: game.answer_correct(is_correct),
            extra_time=lambda game: game.extra_time(),
        )

    @property
    def game_name(self):
        return 'whirligig'

    def get_game(self, token):
        return Game.objects.get(token=token)

    def serialize_game(self, game):
        return GameSerializer().to_representation(game)
