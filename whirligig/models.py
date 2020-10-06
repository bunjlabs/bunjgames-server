import datetime
import time

from django.utils import timezone
import random
import string
from xml.etree import ElementTree

from django.db import models, transaction


class BadFormatException(Exception):
    pass


class BadStateException(Exception):
    pass


class Game(models.Model):
    STATE_START = 'start'
    STATE_INTRO = 'intro'
    STATE_QUESTIONS = 'questions'
    STATE_QUESTION_WHIRLIGIG = 'question_whirligig'
    STATE_QUESTION_START = 'question_start'
    STATE_QUESTION_DISCUSSION = 'question_discussion'
    STATE_ANSWER = 'answer'
    STATE_RIGHT_ANSWER = 'right_answer'
    STATE_QUESTION_END = 'question_end'
    STATE_END = 'end'

    CHOICES_STATE = (
        (STATE_START, STATE_START),
        (STATE_INTRO, STATE_INTRO),
        (STATE_QUESTIONS, STATE_QUESTIONS),
        (STATE_QUESTION_START, STATE_QUESTION_START),
        (STATE_QUESTION_DISCUSSION, STATE_QUESTION_DISCUSSION),
        (STATE_ANSWER, STATE_ANSWER),
        (STATE_RIGHT_ANSWER, STATE_RIGHT_ANSWER),
        (STATE_QUESTION_END, STATE_QUESTION_END),
        (STATE_END, STATE_END),
    )

    MAX_SCORE = 6 + 0

    token = models.CharField(max_length=25, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    expired = models.DateTimeField()
    connoisseurs_score = models.IntegerField(default=0)
    viewers_score = models.IntegerField(default=0)
    cur_item = models.IntegerField(default=None, null=True)
    cur_question = models.IntegerField(default=None, null=True)
    state = models.CharField(max_length=25, choices=CHOICES_STATE, default=STATE_START, blank=True)
    timer_paused = models.BooleanField(default=True)
    timer_paused_time = models.IntegerField(default=0)
    timer_time = models.IntegerField(default=0)

    def get_curr_item(self):
        return self.items.get(number=self.cur_item)

    @staticmethod
    @transaction.atomic(savepoint=False)
    def new():
        token = None
        for i in range(100):
            token = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if Game.objects.filter(token=token).count() == 0:
                break
        if token is None:
            raise Exception('Cannot generate token')
        return Game.objects.create(
            token=token,
            expired=timezone.now() + datetime.timedelta(hours=12)
        )

    @transaction.atomic(savepoint=False)
    def change_score(self, connoisseurs_score, viewers_score):
        if 0 <= connoisseurs_score <= self.MAX_SCORE:
            self.connoisseurs_score = connoisseurs_score
        if 0 <= viewers_score <= self.MAX_SCORE:
            self.viewers_score = viewers_score
        self.save(update_fields=['connoisseurs_score', 'viewers_score'])

    @transaction.atomic(savepoint=False)
    def change_timer(self, paused):
        if self.state != self.STATE_QUESTION_DISCUSSION:
            return
        if paused and not self.timer_paused:
            self.timer_paused_time = int(round(time.time() * 1000))
        elif not paused and self.timer_paused:
            self.timer_time += int(round(time.time() * 1000)) - self.timer_paused_time
            self.timer_paused_time = 0
        self.timer_paused = paused
        self.save(update_fields=['timer_time', 'timer_paused', 'timer_paused_time'])

    @transaction.atomic(savepoint=False)
    def answer_correct(self, is_correct):
        if self.state == self.STATE_RIGHT_ANSWER:
            self.connoisseurs_score += 1 if is_correct else 0
            self.viewers_score += 0 if is_correct else 1

            item = self.items.get(number=self.cur_item)
            question = item.questions.get(number=self.cur_question)
            question.is_processed = True
            question.save()

            if not is_correct or self.cur_question == item.questions.count() - 1:
                item.is_processed = True
                item.save()
                self.cur_item = None
                self.cur_question = None
                if self.connoisseurs_score == self.MAX_SCORE or self.viewers_score == self.MAX_SCORE \
                        or not self.items.filter(is_processed=False).exists():
                    self.state = self.STATE_END
                else:
                    self.state = self.STATE_QUESTION_END
            else:
                self.cur_question += 1
                self.state = self.STATE_QUESTION_START

            self.save()

    @transaction.atomic(savepoint=False)
    def parse(self, filename):
        tree = ElementTree.parse(filename)

        game_xml = tree.getroot()
        items_xml = game_xml.find('items')

        for item_number, item_xml in enumerate(items_xml.findall('item')):
            if item_number >= 13:
                raise BadFormatException()
            item = GameItem.objects.create(
                number=item_number,
                name=item_xml.find('name').text,
                description=item_xml.find('description').text if item_xml.find('description') is not None else '',
                game=self,
                type=item_xml.find('type').text,
            )
            for question_number, question_xml in enumerate(item_xml.find('questions').findall('question')):
                if question_number >= 3:
                    raise BadFormatException()
                answer_xml = question_xml.find('answer')
                question = Question.objects.create(
                    number=question_number,
                    item=item,
                    description=question_xml.find('description').text,
                    text=question_xml.find('text').text,
                    image=question_xml.find('image').text,
                    audio=question_xml.find('audio').text,
                    video=question_xml.find('video').text,

                    answer_description=answer_xml.find('description').text,
                    answer_text=answer_xml.find('text').text,
                    answer_image=answer_xml.find('image').text,
                    answer_audio=answer_xml.find('audio').text,
                    answer_video=answer_xml.find('video').text,
                )

    def print(self):
        for item in self.items.iterator():
            print('Item №{}: name={}, type={}'.format(item.number, item.name, item.type))
            for question in item.questions.iterator():
                print('\tQuestion №{}:'.format(question.number))
                print('\t\tdescription: {}'.format(question.description[:50]))
                print('\t\ttext: {}'.format(question.text[:50] if question.text else None))
                print('\t\timage: {}'.format(question.image))
                print('\t\taudio: {}'.format(question.audio))
                print('\t\tvideo: {}'.format(question.video))
                print()
                print('\tAnswer:')
                print('\t\tdescription: {}'.format(question.answer_description[:50]))
                print('\t\ttext: {}'.format(question.answer_text[:50] if question.answer_text else None))
                print('\t\timage: {}'.format(question.answer_image))
                print('\t\taudio: {}'.format(question.answer_audio))
                print('\t\tvideo: {}'.format(question.answer_video))

    def randomise_next_question(self):
        return random.choice(self.items.filter(is_processed=False).values_list('number', flat=True))

    @transaction.atomic(savepoint=False)
    def next_state(self):
        if self.state == self.STATE_START:
            self.state = self.STATE_INTRO
        elif self.state == self.STATE_INTRO:
            self.state = self.STATE_QUESTIONS
        elif self.state == self.STATE_QUESTIONS:
            self.cur_item = self.randomise_next_question()
            self.cur_question = 0
            self.state = self.STATE_QUESTION_WHIRLIGIG
        elif self.state == self.STATE_QUESTION_WHIRLIGIG:
            self.state = self.STATE_QUESTION_START
        elif self.state == self.STATE_QUESTION_START:
            self.state = self.STATE_QUESTION_DISCUSSION
            self.timer_paused = False
            self.timer_paused_time = 0
            self.timer_time = int(round((time.time() + self.get_curr_item().get_time()) * 1000))
        elif self.state == self.STATE_QUESTION_DISCUSSION:
            self.timer_paused = True
            self.timer_paused_time = 0
            self.timer_time = 0
            self.state = self.STATE_ANSWER
        elif self.state == self.STATE_ANSWER:
            self.state = self.STATE_RIGHT_ANSWER
        elif self.state == self.STATE_RIGHT_ANSWER:
            pass
        elif self.state == self.STATE_QUESTION_END:
            self.cur_item = self.randomise_next_question()
            self.cur_question = 0
            self.state = self.STATE_QUESTION_WHIRLIGIG
        elif self.state == self.STATE_END:
            pass
        else:
            raise BadStateException()
        self.save(update_fields=[
            'state', 'cur_item', 'cur_question', 'timer_paused', 'timer_time', 'timer_paused_time'
        ])

    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]


class GameItem(models.Model):
    TYPE_STANDARD = 'standard'
    TYPE_BLITZ = 'blitz'
    TYPE_SUPERBLITZ = 'superblitz'

    CHOICES_TYPE = (
        (TYPE_STANDARD, TYPE_STANDARD),
        (TYPE_BLITZ, TYPE_BLITZ),
        (TYPE_SUPERBLITZ, TYPE_SUPERBLITZ),
    )

    number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='items')
    type = models.CharField(max_length=25, choices=CHOICES_TYPE)
    is_processed = models.BooleanField(default=False, blank=True)

    def get_time(self):
        return 60 if self.type == self.TYPE_STANDARD else 20


class Question(models.Model):
    number = models.IntegerField()
    item = models.ForeignKey(GameItem, on_delete=models.CASCADE, related_name='questions')
    is_processed = models.BooleanField(default=False, blank=True)

    description = models.TextField()
    text = models.TextField(null=True)
    image = models.CharField(max_length=255, null=True)
    audio = models.CharField(max_length=255, null=True)
    video = models.CharField(max_length=255, null=True)

    answer_description = models.TextField()
    answer_text = models.TextField(null=True)
    answer_image = models.CharField(max_length=255, null=True)
    answer_audio = models.CharField(max_length=255, null=True)
    answer_video = models.CharField(max_length=255, null=True)
