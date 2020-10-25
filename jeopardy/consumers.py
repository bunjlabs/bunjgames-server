from common.consumers import Consumer
from jeopardy.models import Game
from jeopardy.serializers import GameSerializer


class JeopardyConsumer(Consumer):
    @property
    def routes(self):
        return dict(
            next_state=lambda game, from_state: game.next_state(from_state),
            choose_question=lambda game, question_id: game.choose_question(question_id),
            set_answerer_and_bet=lambda game, player_id, bet: game.set_answerer_and_bet(player_id, bet),
            skip_question=lambda game: game.skip_question(),
            button_click=lambda game, player_id: game.button_click(player_id),
            answer=lambda game, is_right: game.answer(is_right),
            remove_final_theme=lambda game, theme_id: game.remove_final_theme(theme_id),
            final_bet=lambda game, player_id, bet: game.final_bet(player_id, bet),
            final_answer=lambda game, player_id, answer: game.final_answer(player_id, answer),
            set_balance=lambda game, balance_list: game.set_balance(balance_list),
            set_round=lambda game, round: game.set_round(round),
        )

    @property
    def game_name(self):
        return 'jeopardy'

    def get_game(self, token):
        return Game.objects.get(token=token)

    def serialize_game(self, game):
        return GameSerializer().to_representation(game)
