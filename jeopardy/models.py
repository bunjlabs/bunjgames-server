import datetime
from xml.etree import ElementTree

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.utils import timezone

from common.utils import generate_token, BadStateException


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
    last_round = models.IntegerField(default=1)
    final_round = models.IntegerField(default=0)  # 0 for no final
    state = models.CharField(max_length=25, choices=CHOICES_STATE, default=STATE_WAITING_FOR_PLAYERS)
    round = models.IntegerField(default=1)
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, related_name='+')
    button_won_by = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')

    def is_final_round(self):
        return self.final_round != 0 and self.round == self.final_round

    def get_categories(self):
        if self.state in (self.STATE_WAITING_FOR_PLAYERS, self.STATE_GAME_END):
            return Category.objects.none()
        if self.state == self.STATE_THEMES_ALL:
            return self.categories.filter(round__in=[
                i for i in range(self.last_round if self.final_round else self.last_round + 1)
            ])
        else:
            return self.categories.filter(round=self.round)

    def generate_token(self):
        self.token = generate_token(self.pk)
        self.save(update_fields=['token'])

    def process_question_end(self):
        self.question.is_processed = True
        self.question.save()
        if Question.objects.filter(category__in=self.get_categories(), is_processed=False).count() > 3 * self.round:
            self.question = None
            self.state = Game.STATE_QUESTIONS
            self.save()
        else:
            self.question = None
            self.state = Game.STATE_THEMES_ROUND
            self.round += 1
            if not self.get_categories().exists():
                self.state = Game.STATE_GAME_END
            self.save()

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        game = Game.objects.create(
            expired=timezone.now() + datetime.timedelta(hours=12)
        )
        game.generate_token()
        return game

    def parse(self, filename):
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

                    if settings.JEOPARDY_IS_POST_EVENT_REQUIRED and right_answer \
                            and not post_text and not post_image and not post_audio and not post_video:
                        post_text = right_answer

                    Question.objects.create(
                        custom_theme=custom_theme,
                        text=text,
                        image=image,
                        audio=audio,
                        video=video,
                        answer_text=post_text,
                        answer_image=post_image,
                        answer_audio=post_audio,
                        answer_video=post_video,
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

    @transaction.atomic(savepoint=False)
    def next_state(self, from_state):
        if from_state is not None and self.state != from_state:
            return
        if self.state == self.STATE_WAITING_FOR_PLAYERS:
            if self.players.count() >= 3:
                self.state = Game.STATE_THEMES_ALL
            else:
                raise BadStateException()
        elif self.state == self.STATE_THEMES_ALL:
            self.state = Game.STATE_THEMES_ROUND
        elif self.state == Game.STATE_THEMES_ROUND:
            self.state = Game.STATE_QUESTIONS
        elif self.state == self.STATE_QUESTIONS:
            pass
        elif self.state == self.STATE_QUESTION_EVENT:
            if self.is_final_round() and self.players.filter(balance__gt=0, final_bet__lte=0).exists():
                raise BadStateException()
            self.state = Game.STATE_QUESTION
        elif self.state == self.STATE_QUESTION:
            pass
        elif self.state == self.STATE_QUESTION_END:
            self.process_question_end()
        elif self.state == self.STATE_FINAL_END:
            self.state = self.STATE_GAME_END
        else:
            raise BadStateException()
        self.save()

    @transaction.atomic(savepoint=False)
    def choose_question(self, question_id):
        question = Question.objects.get(id=question_id)
        if question.category.game.id != self.id or question.is_processed:
            raise BadStateException()
        if self.is_final_round():
            question.is_processed = True
            question.save()

            filtered_question = Question.objects.filter(category__in=self.get_categories(), is_processed=False)
            if filtered_question.count() == 1:
                self.state = Game.STATE_QUESTION_EVENT
                self.question = filtered_question.get()
                self.save()
        else:
            self.state = Game.STATE_QUESTION if question.type == Question.TYPE_STANDARD else Game.STATE_QUESTION_EVENT
            self.question = question
            self.save()

    @transaction.atomic(savepoint=False)
    def end_question(self, player_id, balance_diff):
        if self.is_final_round():
            self.state = Game.STATE_FINAL_END
        else:
            player = self.button_won_by \
                if self.question.type == Question.TYPE_STANDARD else self.players.get(id=player_id)
            player.balance += balance_diff
            player.save()
            self.button_won_by = None

            if self.question.answer_text or self.question.answer_image \
                    or self.question.answer_audio or self.question.answer_video:
                self.state = Game.STATE_QUESTION_END
            else:
                self.process_question_end()
        self.save()

    @transaction.atomic(savepoint=False)
    def skip_question(self):
        if self.state not in (self.STATE_QUESTION_EVENT, self.STATE_QUESTION):
            return

        self.button_won_by = None
        if self.question.answer_text or self.question.answer_image \
                or self.question.answer_audio or self.question.answer_video:
            self.state = Game.STATE_QUESTION_END
        else:
            self.process_question_end()
        self.save()

    @transaction.atomic(savepoint=False)
    def button_click(self, player_id):
        if self.state != self.STATE_QUESTION or self.button_won_by is not None:
            return

        self.button_won_by = self.players.get(id=player_id)
        self.save()

    @transaction.atomic(savepoint=False)
    def final_bet(self, player_id, bet):
        if not self.is_final_round() or self.state != self.STATE_QUESTION_EVENT:
            return
        player = self.players.get(id=player_id)
        if player.balance < bet:
            raise BadStateException()
        player.final_bet = bet
        player.save()

    @transaction.atomic(savepoint=False)
    def final_answer(self, player_id, answer):
        if not self.is_final_round() or self.state != self.STATE_QUESTION:
            return
        player = self.players.get(id=player_id)
        player.final_answer = answer
        player.save()

    @transaction.atomic(savepoint=False)
    def set_balance(self, balance_list):
        for index, player in enumerate(self.players.iterator()):
            player.balance = balance_list[index]
            player.save()

    @transaction.atomic(savepoint=False)
    def set_round(self, round):
        self.round = round
        self.state = Game.STATE_THEMES_ROUND if self.get_categories().exists() else Game.STATE_GAME_END
        self.button_won_by = None
        Question.objects.filter(category__in=self.get_categories(), is_processed=True).update(is_processed=False)
        self.save()


class Category(models.Model):
    name = models.CharField(max_length=255)
    round = models.IntegerField(db_index=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, related_name='categories')

    class Meta:
        ordering = ['round', 'pk']


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

    class Meta:
        ordering = ['pk']


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

    class Meta:
        ordering = ['pk']
