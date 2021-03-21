import datetime
import time
from xml.etree import ElementTree

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from common.utils import generate_token, BadFormatException, BadStateException, NothingToDoException


class Game(models.Model):
    STATE_WAITING_FOR_TEAMS = 'waiting_for_teams'
    STATE_INTRO = 'intro'
    STATE_ROUND = 'round'
    STATE_BUTTON = 'button'
    STATE_ANSWERS = 'answers'
    STATE_ANSWERS_REVEAL = 'answers_reveal'
    STATE_FINAL = 'final'
    STATE_FINAL_QUESTIONS = 'final_questions'
    STATE_FINAL_QUESTIONS_REVEAL = 'final_questions_reveal'
    STATE_END = 'end'

    STATES = (
        STATE_WAITING_FOR_TEAMS,
        STATE_INTRO,
        STATE_ROUND,
        STATE_BUTTON,
        STATE_ANSWERS,
        STATE_ANSWERS_REVEAL,
        STATE_FINAL,
        STATE_FINAL_QUESTIONS,
        STATE_FINAL_QUESTIONS_REVEAL,
        STATE_END,
    )

    CHOICES_STATE = ((o, o) for o in STATES)

    token = models.CharField(max_length=25, null=True, blank=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()
    round = models.IntegerField(default=1)
    state = models.CharField(max_length=25, choices=CHOICES_STATE, default=STATE_WAITING_FOR_TEAMS)
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, related_name='+')
    answerer = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, related_name='+')
    timer = models.BigIntegerField(default=0)

    def get_questions(self):
        return self.questions.filter(
            is_final=self.state in (self.STATE_FINAL, self.STATE_FINAL_QUESTIONS, self.STATE_FINAL_QUESTIONS_REVEAL),
            is_processed=False
        )

    def get_teams(self):
        return self.teams.all()

    def set_timer(self, t):
        self.timer = int(round((time.time() + t) * 1000))

    def clear_timer(self):
        self.set_timer(0)

    def intercom(self, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(f'feud_{self.token}', {
            'type': 'intercom',
            'message': message
        })

    def next_round(self):
        team1 = self.get_teams().first()
        team2 = self.get_teams().last()

        team1.strikes = 0
        team1.save()
        team2.strikes = 0
        team2.save()

        self.question.is_processed = True
        self.question.save()
        if self.get_questions().count() > 0:
            self.round += 1
            self.state = self.STATE_ROUND
            self.answerer = None
        else:
            self.answerer = team1 if team1.score >= team2.score else team2
            self.round = 1
            self.state = self.STATE_FINAL

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        game = Game.objects.create(
            expired=timezone.now() + datetime.timedelta(hours=12)
        )
        game.token = generate_token(game.pk)
        game.save(update_fields=['token'])
        return game

    @transaction.atomic(savepoint=False)
    def parse(self, filename):
        tree = ElementTree.parse(filename)

        game_xml = tree.getroot()
        questions_xml = game_xml.find('questions')

        if len(questions_xml.findall('question')) == 0:
            raise BadFormatException('Game should have at least 1 round')
        for question_xml in questions_xml.findall('question'):
            question = Question.objects.create(
                text=question_xml.find('text').text,
                game=self,
                is_final=False,
            )
            for answer_xml in question_xml.findall('answer'):
                answer = Answer.objects.create(
                    question=question,
                    text=answer_xml.find('text').text,
                    value=int(answer_xml.find('value').text),
                )

        final_questions_xml = game_xml.find('final_questions')

        if len(final_questions_xml.findall('question')) != 5:
            raise BadFormatException('Game should have exactly 5 final questions')
        for question_xml in final_questions_xml.findall('question'):
            question = Question.objects.create(
                text=question_xml.find('text').text,
                game=self,
                is_final=True,
            )
            for answer_xml in question_xml.findall('answer'):
                answer = Answer.objects.create(
                    question=question,
                    text=answer_xml.find('text').text,
                    value=int(answer_xml.find('value').text),
                )
        self.save()

    @transaction.atomic(savepoint=False)
    def next_state(self, from_state=None):
        if from_state is not None and self.state != from_state:
            raise NothingToDoException()
        if self.state == self.STATE_WAITING_FOR_TEAMS:
            if self.teams.count() >= 2:
                self.state = self.STATE_INTRO
            else:
                raise BadStateException('Not enough teams')
        elif self.state == self.STATE_INTRO:
            self.state = self.STATE_ROUND
        elif self.state == self.STATE_ROUND:
            self.state = self.STATE_BUTTON
            self.question = self.get_questions().first()
        elif self.state == self.STATE_BUTTON:
            raise NothingToDoException()
        elif self.state == self.STATE_ANSWERS:
            raise NothingToDoException()
        elif self.state == self.STATE_ANSWERS_REVEAL:
            answer = self.question.answers.filter(is_opened=False).last()
            if answer is None:
                self.next_round()
            else:
                answer.is_opened = True
                answer.save()
                self.intercom('reveal')
        elif self.state == self.STATE_FINAL:
            self.state = self.STATE_FINAL_QUESTIONS
        elif self.state == self.STATE_FINAL_QUESTIONS:
            self.state = self.STATE_FINAL_QUESTIONS_REVEAL
        elif self.state == self.STATE_FINAL_QUESTIONS_REVEAL:
            self.state = self.STATE_FINAL if self.round == 1 else self.STATE_END
            if self.round == 1:
                self.round += 1
            self.answerer.final_score = self.questions.aggregate(sum=Sum('answers__value'))['sum']
            self.answerer.save()
            self.questions.filter(is_final=True, is_processed=True).update(is_processed=False)
        elif self.state == self.STATE_END:
            raise NothingToDoException()
        else:
            raise BadStateException('Bad state')
        self.save()

    def button_click(self, team_id):
        if self.state != Game.STATE_BUTTON or self.answerer is not None:
            raise NothingToDoException()
        with transaction.atomic():
            safe_game = Game.objects.select_for_update().get(id=self.id)
            if safe_game.state != Game.STATE_BUTTON or safe_game.answerer is not None:
                raise NothingToDoException()

            safe_game.answerer = safe_game.teams.get(id=team_id)
            safe_game.save(update_fields=['answerer'])
        self.refresh_from_db()

    @transaction.atomic(savepoint=False)
    def set_answerer(self, team_id=None):
        if self.state != self.STATE_BUTTON:
            raise NothingToDoException()
        answerer = self.get_teams().get(id=team_id)
        self.answerer = answerer
        self.state = self.STATE_ANSWERS
        self.save()

    @transaction.atomic(savepoint=False)
    def answer(self, is_correct, answer_id=None):
        if self.state not in (self.STATE_BUTTON, self.STATE_ANSWERS):
            raise NothingToDoException()

        answerer = self.answerer
        opponent = self.get_teams().exclude(id=answerer.id).get()

        if is_correct:
            answer = self.question.answers.get(id=answer_id)

            if answer.is_opened:
                raise NothingToDoException()

            answer.is_opened = True
            answer.save()

            if self.state == self.STATE_BUTTON:
                self.answerer = opponent
            if self.state == self.STATE_ANSWERS:
                if opponent.strikes >= 3 or self.question.answers.filter(is_opened=False).count() == 0:
                    answerer.score += self.question.answers.filter(is_opened=True).aggregate(sum=Sum('value'))['sum']
                    answerer.save()
                    self.state = self.STATE_ANSWERS_REVEAL
            if self.state == self.STATE_FINAL_QUESTIONS:
                self.question.is_processed = True
                self.question.save()
                self.question = self.get_questions().first()
        elif self.state == self.STATE_BUTTON:
            self.answerer = opponent
        elif self.state == self.STATE_ANSWERS:
            answerer.strikes += 1
            answerer.save()

            if self.state == self.STATE_BUTTON:
                self.answerer = opponent
            if self.state == self.STATE_ANSWERS:
                if opponent.strikes >= 3:
                    opponent.score += self.question.answers.filter(is_opened=True).aggregate(sum=Sum('value'))['sum']
                    opponent.save()
                    self.state = self.STATE_ANSWERS_REVEAL
                elif answerer.strikes >= 3:
                    self.answerer = opponent
            if self.state == self.STATE_FINAL_QUESTIONS:
                self.question.is_processed = True
                self.question.save()
                self.question = self.get_questions().first()
        if not is_correct:
            self.intercom('gong')
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]


class Question(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    is_final = models.BooleanField()
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['is_final']),
            models.Index(fields=['is_processed']),
        ]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    value = models.IntegerField()
    is_opened = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['is_opened']),
        ]


class Team(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='teams')
    name = models.TextField()
    strikes = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']
