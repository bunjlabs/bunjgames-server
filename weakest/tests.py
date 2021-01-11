from django.test import TestCase

from weakest.models import Game, Player


class WeakestTestCase(TestCase):

    def test_weakest_choose(self):
        game = Game.new()
        game.state = game.STATE_WEAKEST_CHOOSE
        game.save()

        player1 = Player.objects.create(game=game, name="1", right_answers=4, bank_income=4)
        player2 = Player.objects.create(game=game, name="2", right_answers=3, bank_income=10)
        player3 = Player.objects.create(game=game, name="3", right_answers=1, bank_income=5)
        player4 = Player.objects.create(game=game, name="4", right_answers=3, bank_income=2)

        self.assertEqual(game.get_weakest().id, player3.id)
        self.assertEqual(game.get_strongest().id, player1.id)

        player1.is_weak = True
        player1.save()
        player3.is_weak = True
        player3.save()
        # game.refresh_from_db()

        self.assertEqual(game.get_weakest().id, player4.id)
        self.assertEqual(game.get_strongest().id, player2.id)

    def test_weakest_reveal(self):
        game = Game.new()
        game.state = game.STATE_WEAKEST_REVEAL
        game.save()

        player1 = Player.objects.create(game=game, name="1", right_answers=4, bank_income=4)
        player2 = Player.objects.create(game=game, name="2", right_answers=3, bank_income=10)
        player3 = Player.objects.create(game=game, name="3", right_answers=1, bank_income=5)
        player4 = Player.objects.create(game=game, name="4", right_answers=3, bank_income=2)

        player1.weak = player2
        player1.save()
        player2.weak = player3
        player2.save()
        player3.weak = player4
        player3.save()
        player4.weak = player1
        player4.save()

        self.assertEqual(game.get_weakest().id, player3.id)

        player1.weak = player2
        player1.save()
        player2.weak = player4
        player2.save()
        player3.weak = player4
        player3.save()
        player4.weak = player2
        player4.save()

        self.assertEqual(game.get_weakest().id, player4.id)

        player1.weak = player3
        player1.save()
        player2.weak = player1
        player2.save()
        player3.weak = player1
        player3.save()
        player4.weak = player1
        player4.save()

        self.assertEqual(game.get_weakest().id, player1.id)
