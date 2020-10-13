import datetime
import random
import string
from xml.etree import ElementTree

from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.utils import timezone

from common.utils import generate_token


class Game(models.Model):
    STATE_WAITING_FOR_PLAYERS = 'waiting_for_players'
    STATE_THEMES_ALL = 'themes_all'
    STATE_THEMES_ROUND = 'themes_round'
    STATE_QUESTIONS = 'questions'
    STATE_QUESTION_EVENT = 'question_event'
    STATE_QUESTION = 'question'
    STATE_QUESTION_END = 'question_end'
    STATE_FINAL_END = 'final_end'
    STATE_GAME_END = 'game_end'

    STATES = (
        STATE_WAITING_FOR_PLAYERS,
        STATE_THEMES_ALL,
        STATE_THEMES_ROUND,
        STATE_QUESTIONS,
        STATE_QUESTION_EVENT,
        STATE_QUESTION,
        STATE_QUESTION_END,
        STATE_FINAL_END,
        STATE_GAME_END,
    )

    CHOICES_STATE = ((o, o) for o in STATES)

    token = models.CharField(max_length=25, null=True, blank=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, related_name='+')
    round = models.IntegerField(default=1)
    last_round = models.IntegerField(default=1)
    final_round = models.IntegerField(default=0)  # 0 for no final
    state = models.CharField(max_length=25, choices=CHOICES_STATE, default=STATE_WAITING_FOR_PLAYERS)
    button_won_by = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')

    def get_current_categories(self):
        return self.categories.filter(round=self.round)

    def get_all_categories(self):
        return self.categories.all()

    def generate_token(self):
        self.token = generate_token(self.pk)
        self.save(update_fields=['token'])

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        game = Game.objects.create(
            expired=timezone.now() + datetime.timedelta(hours=12)
        )
        game.generate_token()
        return game

    def parse_xml(self, filename):
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        namespace = root.tag.replace('}package', '}')

        last_round = 0

        for i, round in enumerate(root.find(namespace + 'rounds').findall(namespace + 'round')):
            last_round = i + 1
            for theme in round.find(namespace + 'themes').findall(namespace + 'theme'):
                theme_name = theme.get('name')
                category = Category.objects.create(name=theme_name, round=i+1, game=self)
                for question in theme.find(namespace + 'questions').findall(namespace + 'question'):
                    question_price = question.get('price')
                    type = Question.TYPE_STANDARD
                    custom_theme = None
                    if question.find(namespace + 'type') is not None:
                        if question.find(namespace + 'type').get('name') == 'auction':
                            type = Question.TYPE_AUCTION
                        elif question.find(namespace + 'type').get('name') == 'cat' \
                                or question.find(namespace + 'type').get('name') == 'bagcat':
                            type = Question.TYPE_BAG_CAT
                            for param in question.find(namespace + 'type').findall('param'):
                                if param.get('name') == 'theme':
                                    custom_theme = param.text
                    text = ''
                    image = None
                    audio = None
                    video = None

                    marker_flag = False
                    post_text = None
                    post_image = None
                    post_audio = None
                    post_video = None

                    for atom in question.find(namespace + 'scenario').findall(namespace + 'atom'):
                        if atom.get('type') == 'image':
                            if marker_flag:
                                post_image = atom.text
                            else:
                                image = atom.text
                        elif atom.get('type') == 'voice':
                            if marker_flag:
                                post_audio = atom.text
                            else:
                                audio = atom.text
                        elif atom.get('type') == 'video':
                            if marker_flag:
                                post_video = atom.text
                            else:
                                video = atom.text
                        elif atom.get('type') == 'marker':
                            marker_flag = True
                        elif atom.text:
                            if marker_flag:
                                post_text = atom.text
                            else:
                                text = atom.text

                    right_answer = ''
                    for answer in question.find(namespace + 'right').findall(namespace + 'answer'):
                        right_answer += (answer.text + '   ') if answer.text else ''
                    right_answer = right_answer.strip()
                    comment = ''
                    if question.find(namespace + 'info') is not None \
                            and question.find(namespace + 'info').find(namespace + 'comments') is not None:
                        comment = question.find(namespace + 'info').find(namespace + 'comments').text

                    if IS_POST_EVENT_REQUIRED and right_answer \
                            and not post_text and not post_image and not post_audio and not post_video:
                        post_text = right_answer

                    Question.objects.create(
                        custom_theme=custom_theme,
                        text=text,
                        image=image,
                        audio=audio,
                        video=video,
                        post_text=post_text,
                        post_image=post_image,
                        post_audio=post_audio,
                        post_video=post_video,
                        value=question_price,
                        answer=right_answer,
                        comment=comment,
                        type=type,
                        category=category
                    )
        self.last_round = last_round
        if self.categories.filter(round=last_round)[0].questions.count() == 1:
            self.final_round = last_round
        self.save()


class Player(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    balance = models.IntegerField(default=0)
    final_bet = models.IntegerField(default=0)
    final_answer = models.TextField(default='', blank=True)

    @staticmethod
    def get_by_game_and_name(game, name):
        try:
            return Player.objects.get(
                game=game, name=name
            )
        except ObjectDoesNotExist:
            return None


class Category(models.Model):
    name = models.CharField(max_length=255)
    round = models.IntegerField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, related_name='categories')


class Question(models.Model):
    TYPE_STANDARD = 'standard'
    TYPE_AUCTION = 'auction'
    TYPE_BAG_CAT = 'bagcat'

    TYPES = (
        TYPE_STANDARD,
        TYPE_AUCTION,
        TYPE_BAG_CAT
    )

    CHOICES_TYPE = ((o, o) for o in TYPES)

    custom_theme = models.CharField(max_length=255, null=True)
    text = models.TextField(null=True)
    image = models.CharField(max_length=255, null=True)
    audio = models.CharField(max_length=255, null=True)
    video = models.CharField(max_length=255, null=True)
    answer = models.CharField(max_length=255)
    answer_text = models.TextField(null=True)
    answer_image = models.CharField(max_length=255, null=True)
    answer_audio = models.CharField(max_length=255, null=True)
    answer_video = models.CharField(max_length=255, null=True)
    value = models.IntegerField()
    comment = models.TextField()
    type = models.CharField(max_length=25, choices=CHOICES_TYPE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='questions')
    is_processed = models.BooleanField(default=False)
