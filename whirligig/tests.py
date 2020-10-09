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


# class GameAPITestCase(APITestCase):
#     CREATE_GAME_URL = reverse('create_game')
#     GAME_URL = reverse('game')
#     NEXT_STATE_URL = reverse('next_state')
#
#     def test_game_api(self):
#         # Creating game
#         with open('game.whirligig', 'rb') as file:
#             response = self.client.post(self.CREATE_GAME_URL, dict(game=file), format="multipart")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         game = response.json()
#         self.assertGreater(len(game['token']), 0)
#
#         # Retrieving game
#         response = self.client.get(self.GAME_URL, dict(token=game['token']))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['token'], game['token'])
#         self.assertEqual(response.json()['state'], Game.STATE_START)
#
#         # Iterating through game states
#         response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['state'], Game.STATE_INTRO)
#
#         response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.json()['state'], Game.STATE_QUESTIONS)
#
#         for item in game['items']:
#             response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#             self.assertEqual(response.status_code, status.HTTP_200_OK)
#             self.assertEqual(response.json()['state'], Game.STATE_QUESTION_WHIRLIGIG)
#
#             for question in item['questions']:
#                 response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#                 self.assertEqual(response.status_code, status.HTTP_200_OK)
#                 self.assertEqual(response.json()['state'], Game.STATE_QUESTION_START)
#
#                 response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#                 self.assertEqual(response.status_code, status.HTTP_200_OK)
#                 self.assertEqual(response.json()['state'], Game.STATE_QUESTION_DISCUSSION)
#
#                 response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#                 self.assertEqual(response.status_code, status.HTTP_200_OK)
#                 self.assertEqual(response.json()['state'], Game.STATE_QUESTION_END)
#
#                 response = self.client.post(self.NEXT_STATE_URL, dict(token=game['token']))
#                 self.assertEqual(response.status_code, status.HTTP_200_OK)
#                 self.assertTrue(response.json()['state'] in (Game.STATE_QUESTIONS, Game.STATE_END))
#
#         self.assertEqual(response.json()['state'], Game.STATE_END)
#         for item_inner in response.json()['items']:
#             self.assertTrue(item_inner['is_processed'])
#             for question_inner in item_inner['questions']:
#                 self.assertTrue(question_inner['is_processed'])

