from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from whirligig.models import Game


class GameXMLParsingTestCase(TestCase):

    def test_parse_game_xml(self):
        game = Game.new()
        game.parse('content.xml')
        self.assertGreater(game.items.count(), 0)
        for item in game.items.iterator():
            self.assertGreater(item.questions.count(), 0)
            for question in item.questions.iterator():
                self.assertGreater(len(question.description), 0)
                self.assertGreater(len(question.answer_description), 0)


class GameAPITestCase(APITestCase):
    CREATE_GAME_URL = reverse('create_game')
    GAME_URL = reverse('game')

    def test_create_and_get_game(self):
        with open('game.whirligig', 'rb') as file:
            response = self.client.post(self.CREATE_GAME_URL, data=dict(game=file), format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        game = response.json()
        self.assertGreater(len(game['token']), 0)

        response = self.client.get(self.GAME_URL, data=dict(token=game['token']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['token'], game['token'])
