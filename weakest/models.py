import datetime
import time
from xml.etree import ElementTree

from django.db import models, transaction
from django.db.models import Count, Q, F, Subquery, OuterRef
from django.utils import timezone

from common.utils import generate_token, BadFormatException, BadStateException, NothingToDoException


class Game(models.Model):
    STATE_WAITING_FOR_PLAYERS = 'waiting_for_players'
    STATE_INTRO = 'intro'
    STATE_ROUND = 'round'
    STATE_QUESTIONS = 'questions'
    STATE_WEAKEST_CHOOSE = 'weakest_choose'
    STATE_WEAKEST_REVEAL = 'weakest_reveal'
    STATE_FINAL = 'final'
    STATE_FINAL_QUESTIONS = 'final_questions'
    STATE_END = 'end'

    STATES = (
        STATE_WAITING_FOR_PLAYERS,
        STATE_INTRO,
        STATE_QUESTIONS,
        STATE_WEAKEST_CHOOSE,
        STATE_WEAKEST_REVEAL,
        STATE_FINAL,
        STATE_FINAL_QUESTIONS,
        STATE_END,
    )

    CHOICES_STATE = ((o, o) for o in STATES)

    token = models.CharField(max_length=25, null=True, blank=True, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()
    score_multiplier = models.IntegerField(default=1)
    score = models.IntegerField(default=0)
    bank = models.IntegerField(default=0)
    tmp_score = models.IntegerField(default=0)
    round = models.IntegerField(default=1)
    state = models.CharField(max_length=25, choices=CHOICES_STATE, default=STATE_WAITING_FOR_PLAYERS)
    question = models.ForeignKey('Question', on_delete=models.SET_NULL, null=True, related_name='+')
    answerer = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')
    weakest = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')
    strongest = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')
    timer = models.BigIntegerField(default=0)
    bank_timer = models.BigIntegerField(default=0)

    def get_questions(self):
        return self.questions.filter(is_final=self.state == self.STATE_FINAL_QUESTIONS, is_processed=False)

    def get_players(self):
        return self.players.filter(is_weak=False)

    def generate_token(self):
        self.token = generate_token(self.pk)

    def set_timer(self, t):
        self.timer = int(round((time.time() + t) * 1000))

    def clear_timer(self):
        self.set_timer(0)

    def set_bank_timer(self, t):
        self.bank_timer = int(round((time.time() + t) * 1000))

    def next_round(self):
        self.round += 1
        self.bank = 0

    @transaction.atomic(savepoint=False)
    def next_question(self, answerer=None, is_correct=None):
        if self.question:
            question = self.question
            question.is_processed = True
            if is_correct is not None:
                question.is_correct = is_correct
            question.save()
        self.question = self.get_questions().first()
        if not self.question and self.state in (self.STATE_FINAL, self.STATE_FINAL_QUESTIONS):
            self.answerer = None
            self.state = self.STATE_END
        elif not self.question:
            self.save_bank(force=True)
            self.round_end()
        else:
            if answerer:
                self.answerer = answerer
            elif self.answerer:
                players = list(self.get_players())
                self.answerer = players[
                    (next(i for i, p in enumerate(players) if p.id == self.answerer.id) + 1) % len(players)
                ]
            elif self.strongest and not self.strongest.is_weak:
                self.answerer = self.strongest
            else:
                self.answerer = self.get_players().order_by('name').first()
            self.set_bank_timer(3)

    def round_end(self):
        self.clear_timer()
        self.score += self.bank
        self.tmp_score = 0
        self.answerer = None
        self.weakest = self.get_weakest()
        self.strongest = self.get_strongest()
        self.state = self.STATE_WEAKEST_CHOOSE

    def get_next_tmp_score(self):
        scores = [0, 1, 2, 5, 10, 15, 20, 30, 40]
        return scores[scores.index(self.tmp_score) + 1]

    def get_weakest(self):
        if self.state == self.STATE_WEAKEST_REVEAL:
            players = self.players.filter(is_weak=False)
            return players.annotate(
                count=Subquery(
                    players.filter(
                        weak_id=OuterRef('id')
                    ).order_by().values('weak_id').annotate(c=Count('weak_id')).values('c'),
                    output_field=models.IntegerField()
                )
            ).filter(count__isnull=False).order_by(
                '-count', 'right_answers', 'bank_income'
            ).first()
        else:
            return self.players.filter(is_weak=False).order_by(
                'right_answers', 'bank_income'
            ).first()

    def get_strongest(self):
        return self.players.filter(is_weak=False).order_by(
            '-right_answers', '-bank_income'
        ).first()

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        game = Game.objects.create(
            expired=timezone.now() + datetime.timedelta(hours=12)
        )
        game.generate_token()
        game.save()
        return game

    @transaction.atomic(savepoint=False)
    def parse(self, filename):
        tree = ElementTree.parse(filename)

        game_xml = tree.getroot()
        questions_xml = game_xml.find('questions')

        for question_number, question_xml in enumerate(questions_xml.findall('question')):
            question = Question.objects.create(
                question=question_xml.find('question').text,
                answer=question_xml.find('answer').text,
                game=self,
                is_final=False,
            )

        final_questions_xml = game_xml.find('final_questions')

        if len(final_questions_xml.findall('question')) < 10:
            raise BadFormatException('Number of final questions must be 10 or more')
        for question_number, question_xml in enumerate(final_questions_xml.findall('question')):
            question = Question.objects.create(
                question=question_xml.find('question').text,
                answer=question_xml.find('answer').text,
                game=self,
                is_final=True,
            )

        score_multiplier_xml = game_xml.find('score_multiplier')
        self.score_multiplier = int(score_multiplier_xml.text)
        self.save()

    @transaction.atomic(savepoint=False)
    def next_state(self, from_state=None):
        if from_state is not None and self.state != from_state:
            raise NothingToDoException()
        if self.state == self.STATE_WAITING_FOR_PLAYERS:
            if self.players.count() >= 3:
                self.state = self.STATE_INTRO
            else:
                raise BadStateException('Not enough players')
        elif self.state == self.STATE_INTRO:
            self.state = self.STATE_ROUND
        elif self.state == self.STATE_ROUND:
            self.get_players().update(right_answers=0, bank_income=0)
            self.state = self.STATE_QUESTIONS
            self.set_timer(150 - (self.round - 1) * 10)
            self.next_question()
        elif self.state == self.STATE_QUESTIONS:
            self.round_end()
        elif self.state == self.STATE_WEAKEST_CHOOSE:
            raise NothingToDoException()
        elif self.state == self.STATE_WEAKEST_REVEAL:
            weakest = self.weakest
            weakest.is_weak = True
            weakest.save()
            self.weakest = None
            self.players.filter(is_weak=False).update(weak=None)
            if self.players.filter(is_weak=False).count() > 2:
                self.state = self.STATE_ROUND
                self.next_round()
            else:
                self.state = self.STATE_FINAL
                self.next_round()
        elif self.state == self.STATE_FINAL:
            raise NothingToDoException()
        elif self.state == self.STATE_FINAL_QUESTIONS:
            raise NothingToDoException()
        elif self.state == self.STATE_END:
            raise NothingToDoException()
        else:
            raise BadStateException('Bad state')
        self.save()

    @transaction.atomic(savepoint=False)
    def save_bank(self, force=False):
        if self.state != self.STATE_QUESTIONS:
            raise NothingToDoException()
        if not force and self.bank_timer < time.time() * 1000:
            raise NothingToDoException()
        player = self.answerer
        player.bank_income += self.tmp_score if self.bank + self.tmp_score <= 40 else 40 - self.bank
        player.save()
        self.bank += self.tmp_score
        self.tmp_score = 0
        if self.bank >= 40:
            self.bank = 40
            self.round_end()
        self.save()

    @transaction.atomic(savepoint=False)
    def answer_correct(self, is_correct):
        if self.state not in (self.STATE_QUESTIONS, self.STATE_FINAL_QUESTIONS):
            raise NothingToDoException()
        if is_correct:
            player = self.answerer
            player.right_answers += 1
            player.save()
            if self.state == self.STATE_QUESTIONS:
                self.tmp_score = self.get_next_tmp_score()
                if self.tmp_score == 40:
                    self.save_bank(force=True)
                    self.round_end()
                    self.save()
                    return
        elif self.state == self.STATE_QUESTIONS:
            self.tmp_score = 0

        if self.state == self.STATE_FINAL_QUESTIONS:
            player_a = self.get_players()[0]
            player_b = self.get_players()[1]
            questions_count = self.questions.filter(is_final=True, is_processed=True).count()
            right_answers_diff = abs(player_a.right_answers - player_b.right_answers)
            if questions_count < 10 and right_answers_diff >= 3 or questions_count == 9 and right_answers_diff > 0:
                self.answerer = player_a if player_a.right_answers > player_b.right_answers else player_b
                self.state = self.STATE_END
                self.save()
                return
            elif questions_count >= 10 and questions_count % 2 == 1:
                last_question = self.questions.filter(is_final=True, is_processed=True).last()
                if is_correct and not last_question.is_correct:
                    self.state = self.STATE_END
                    self.save()
                    return
                elif not is_correct and last_question.is_correct:
                    self.answerer = player_a if player_a.id != self.answerer.id else player_b
                    self.state = self.STATE_END
                    self.save()
                    return
        self.next_question(is_correct=is_correct)
        self.save()

    @transaction.atomic(savepoint=False)
    def select_weakest(self, player_id, weakest_id):
        if self.state != self.STATE_WEAKEST_CHOOSE:
            raise NothingToDoException()
        player = self.players.get(id=player_id)
        player.weak = self.players.get(id=weakest_id)
        if player.is_weak or player.weak.is_weak:
            raise BadStateException('Cannot vote for weak player')
        player.save()
        if self.players.filter(is_weak=False, weak=None).count() == 0:
            self.state = self.STATE_WEAKEST_REVEAL
            self.weakest = self.get_weakest()
            self.save()

    @transaction.atomic(savepoint=False)
    def select_final_answerer(self, player_id):
        if self.state != self.STATE_FINAL:
            raise NothingToDoException()
        self.get_players().update(right_answers=0, bank_income=0)
        answerer = self.players.get(id=player_id)
        self.state = self.STATE_FINAL_QUESTIONS
        self.next_question(answerer=answerer)
        self.save()

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]


class Question(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    answer = models.TextField()
    is_final = models.BooleanField()
    is_answered_correctly = models.BooleanField(null=True)
    is_processed = models.BooleanField(default=False)
    is_correct = models.BooleanField(null=True)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['is_final']),
            models.Index(fields=['is_processed']),
        ]


class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    name = models.TextField()
    is_weak = models.BooleanField(default=False)
    weak = models.ForeignKey('Player', on_delete=models.SET_NULL, null=True, related_name='+')
    right_answers = models.IntegerField(default=0)
    bank_income = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['is_weak']),
        ]
