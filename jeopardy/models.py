import datetime
from xml.etree import ElementTree

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.utils import timezone

from common.utils import generate_token, BadStateException, NothingToDoException


class Game(models.Model):
    STATE_WAITING_FOR_PLAYERS = 'waiting_for_players'
    STATE_INTRO = 'intro'
    STATE_THEMES_ALL = 'themes_all'
    STATE_ROUND = 'round'
    STATE_ROUND_THEMES = 'round_themes'
    STATE_QUESTIONS = 'questions'
    STATE_QUESTION_EVENT = 'question_event'
    STATE_QUESTION = 'question'
    STATE_ANSWER = 'answer'
    STATE_QUESTION_END = 'question_end'
    STATE_FINAL_THEMES = 'final_themes'
    STATE_FINAL_BETS = 'final_bets'
    STATE_FINAL_QUESTION = 'final_question'
    STATE_FINAL_ANSWER = 'final_answer'
    STATE_FINAL_PLAYER_ANSWER = 'final_player_answer'
    STATE_FINAL_PLAYER_BET = 'final_player_bet'
    STATE_GAME_END = 'game_end'

    STATES = (
        STATE_WAITING_FOR_PLAYERS,
        STATE_INTRO,
        STATE_THEMES_ALL,
        STATE_ROUND,
        STATE_ROUND_THEMES,
        STATE_QUESTIONS,
        STATE_QUESTION_EVENT,
        STATE_QUESTION,
        STATE_ANSWER,
        STATE_QUESTION_END,
        STATE_FINAL_THEMES,
        STATE_FINAL_BETS,
        STATE_FINAL_QUESTION,
        STATE_FINAL_ANSWER,
        STATE_FINAL_PLAYER_ANSWER,
        STATE_FINAL_PLAYER_BET,
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
    answerer = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')
    question_bet = models.IntegerField(default=0)

    def is_final_round(self):
        return self.final_round != 0 and self.round == self.final_round

    def get_themes(self):
        if self.state in (self.STATE_WAITING_FOR_PLAYERS, self.STATE_GAME_END):
            return Theme.objects.none()
        if self.state == self.STATE_THEMES_ALL:
            return self.themes.filter(round__in=[
                i for i in range(self.last_round if self.final_round else self.last_round + 1)
            ])
        else:
            return self.themes.filter(round=self.round)

    def generate_token(self):
        self.token = generate_token(self.pk)
        self.save(update_fields=['token'])

    def process_question_end(self):
        self.question.is_processed = True
        self.question.save()
        if Question.objects.filter(theme__in=self.get_themes(), is_processed=False).count() > 0:
            self.question = None
            self.state = self.STATE_QUESTIONS
            self.save()
        else:
            self.question = None
            self.state = self.STATE_ROUND
            self.round += 1
            if not self.get_themes().exists():
                self.state = self.STATE_GAME_END
            self.save()

    def next_final_end_state(self):
        answerers = self.players.filter(final_bet__gt=0)
        if answerers.count() > 0:
            self.answerer = answerers.first()
            self.state = self.STATE_FINAL_PLAYER_ANSWER
        else:
            self.state = self.STATE_GAME_END

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        game = Game.objects.create(
            expired=timezone.now() + datetime.timedelta(hours=12)
        )
        game.generate_token()
        return game

    @transaction.atomic(savepoint=False)
    def parse(self, filename):
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        namespace = root.tag.replace('}package', '}')

        last_round = 0

        def format_image_url(url: str):
            if url and url.startswith('@'):
                return '/Images' + url.replace('@', '/', 1)
            return url

        def format_audio_url(url: str):
            if url and url.startswith('@'):
                return '/Audio' + url.replace('@', '/', 1)
            return url

        def format_video_url(url: str):
            if url and url.startswith('@'):
                return '/Video' + url.replace('@', '/', 1)
            return url

        for i, round in enumerate(root.find(namespace + 'rounds').findall(namespace + 'round')):
            last_round = i + 1
            for theme in round.find(namespace + 'themes').findall(namespace + 'theme'):
                theme_name = theme.get('name')
                theme_model = Theme.objects.create(name=theme_name, round=i+1, game=self)
                if theme.find(namespace + 'questions') is None:
                    continue
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
                        image=format_image_url(image),
                        audio=format_audio_url(audio),
                        video=format_video_url(video),
                        answer_text=post_text,
                        answer_image=format_image_url(post_image),
                        answer_audio=format_audio_url(post_audio),
                        answer_video=format_video_url(post_video),
                        value=question_price,
                        answer=right_answer,
                        comment=comment,
                        type=type,
                        theme=theme_model
                    )
        self.last_round = last_round
        if self.themes.filter(round=last_round)[0].questions.count() == 1:
            self.final_round = last_round
        self.save()

    @transaction.atomic(savepoint=False)
    def next_state(self, from_state):
        if from_state is not None and self.state != from_state:
            raise NothingToDoException()
        if self.state == self.STATE_WAITING_FOR_PLAYERS:
            if self.players.count() >= 3:
                self.state = self.STATE_INTRO
            else:
                raise BadStateException('Not enough players')
        elif self.state == self.STATE_INTRO:
            self.state = self.STATE_THEMES_ALL
        elif self.state == self.STATE_THEMES_ALL:
            self.state = self.STATE_ROUND
        elif self.state == self.STATE_ROUND:
            if self.is_final_round():
                self.state = self.STATE_FINAL_THEMES
            else:
                self.state = self.STATE_ROUND_THEMES
        elif self.state == self.STATE_ROUND_THEMES:
            self.state = self.STATE_QUESTIONS
        elif self.state == self.STATE_QUESTIONS:
            raise NothingToDoException()
        elif self.state == self.STATE_QUESTION_EVENT:
            raise NothingToDoException()
        elif self.state == self.STATE_QUESTION:
            self.state = self.STATE_ANSWER
        elif self.state == self.STATE_ANSWER:
            raise NothingToDoException()
        elif self.state == self.STATE_QUESTION_END:
            self.process_question_end()
        elif self.state == self.STATE_FINAL_THEMES:
            raise NothingToDoException()
        elif self.state == self.STATE_FINAL_BETS:
            if self.is_final_round() and self.players.filter(balance__gt=0, final_bet__lte=0).exists():
                raise BadStateException('Wait for all bets')
            self.state = self.STATE_FINAL_QUESTION
        elif self.state == self.STATE_FINAL_QUESTION:
            self.state = self.STATE_FINAL_ANSWER
        elif self.state == self.STATE_FINAL_ANSWER:
            self.next_final_end_state()
        elif self.state == self.STATE_FINAL_PLAYER_ANSWER:
            raise NothingToDoException()
        elif self.state == self.STATE_FINAL_PLAYER_BET:
            answerer = self.answerer
            answerer.final_bet = 0
            answerer.save()
            self.answerer = None
            self.next_final_end_state()
        else:
            raise BadStateException('Bad state')
        self.save()

    @transaction.atomic(savepoint=False)
    def choose_question(self, question_id):
        question = Question.objects.get(id=question_id)
        if question.theme.game.id != self.id or question.is_processed:
            raise BadStateException('Question is already processed')
        self.state = self.STATE_QUESTION if question.type == Question.TYPE_STANDARD else self.STATE_QUESTION_EVENT
        self.question = question
        self.save()

    @transaction.atomic(savepoint=False)
    def set_answerer_and_bet(self, player_id, bet):
        if self.state != self.STATE_QUESTION_EVENT:
            raise NothingToDoException()
        if bet <= 0:
            raise BadStateException('Bet must be more than 0')

        self.question_bet = bet
        self.answerer = self.players.get(id=player_id)
        self.state = self.STATE_QUESTION
        self.save()

    @transaction.atomic(savepoint=False)
    def skip_question(self):
        if self.state not in (self.STATE_QUESTION_EVENT, self.STATE_QUESTION, self.STATE_ANSWER):
            raise NothingToDoException()

        self.question_bet = 0
        self.answerer = None

        if self.question.answer_text or self.question.answer_image \
                or self.question.answer_audio or self.question.answer_video:
            self.state = self.STATE_QUESTION_END
        else:
            self.process_question_end()
        self.save()
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'jeopardy_{self.token}', {
            'type': 'intercom',
            'message': 'skip'
        })

    @transaction.atomic(savepoint=False)
    def button_click(self, player_id):
        if self.state != self.STATE_ANSWER or self.answerer is not None \
                or self.question.type != Question.TYPE_STANDARD:
            raise NothingToDoException()

        self.answerer = self.players.get(id=player_id)
        self.save()

    @transaction.atomic(savepoint=False)
    def answer(self, is_right):
        if self.state != self.STATE_ANSWER or self.answerer is None:
            raise NothingToDoException()

        def question_end():
            self.question_bet = 0

            if self.question.answer_text or self.question.answer_image \
                    or self.question.answer_audio or self.question.answer_video:
                self.state = Game.STATE_QUESTION_END
            else:
                self.process_question_end()

        if is_right:
            player = self.answerer
            player.balance += self.question_bet if self.question.type != Question.TYPE_STANDARD else self.question.value
            player.save()
            question_end()
        else:
            player = self.answerer
            player.balance -= self.question_bet if self.question.type != Question.TYPE_STANDARD else self.question.value
            player.save()
            if self.question.type != Question.TYPE_STANDARD:
                question_end()
        self.answerer = None
        self.save()

    @transaction.atomic(savepoint=False)
    def remove_final_theme(self, theme_id):
        if self.state != self.STATE_FINAL_THEMES:
            raise NothingToDoException()
        theme = self.get_themes().get(id=theme_id)
        theme.is_removed = True
        theme.save()

        filtered_themes = self.get_themes().filter(is_removed=False)
        if filtered_themes.count() == 1:
            self.state = self.STATE_FINAL_BETS
            self.question = filtered_themes.get().questions.get()
            self.save()

    @transaction.atomic(savepoint=False)
    def final_bet(self, player_id, bet):
        if self.state != self.STATE_FINAL_BETS:
            raise NothingToDoException()
        player = self.players.get(id=player_id)
        if bet <= 0:
            raise BadStateException('Bet must be more than 0')
        if player.balance < bet:
            raise BadStateException('Not enough money')
        player.final_bet = bet
        player.save()

    @transaction.atomic(savepoint=False)
    def final_answer(self, player_id, answer):
        if self.state != self.STATE_FINAL_ANSWER:
            raise NothingToDoException()
        if not answer:
            raise BadStateException('Answer cannot be empty')
        player = self.players.get(id=player_id)
        player.final_answer = answer
        player.save()

    @transaction.atomic(savepoint=False)
    def final_player_answer(self, is_right):
        if self.state != self.STATE_FINAL_PLAYER_ANSWER:
            raise NothingToDoException()
        answerer = self.answerer
        answerer.balance += answerer.final_bet if is_right else -answerer.final_bet
        answerer.save()

        self.state = self.STATE_FINAL_PLAYER_BET
        self.save()

    @transaction.atomic(savepoint=False)
    def set_balance(self, balance_list):
        for index, player in enumerate(self.players.iterator()):
            player.balance = balance_list[index]
            player.save()

    @transaction.atomic(savepoint=False)
    def set_round(self, round):
        self.round = round
        if self.get_themes().exists():
            self.state = self.STATE_ROUND
        else:
            self.state = self.STATE_GAME_END
        self.answerer = None
        self.question_bet = 0
        Question.objects.filter(theme__in=self.get_themes(), is_processed=True).update(is_processed=False)
        self.get_themes().filter(is_removed=True).update(is_removed=False)
        self.save()


class Theme(models.Model):
    name = models.CharField(max_length=255)
    round = models.IntegerField(db_index=True)
    is_removed = models.BooleanField(default=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, related_name='themes')

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
    image = models.TextField(null=True)
    audio = models.TextField(null=True)
    video = models.TextField(null=True)
    answer = models.TextField()
    answer_text = models.TextField(null=True)
    answer_image = models.TextField(null=True)
    answer_audio = models.TextField(null=True)
    answer_video = models.TextField(null=True)
    value = models.IntegerField()
    comment = models.TextField()
    type = models.CharField(max_length=25, choices=CHOICES_TYPE)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='questions')
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
