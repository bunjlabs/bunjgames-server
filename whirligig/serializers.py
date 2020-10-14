from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from whirligig.models import Game, GameItem, Question


class QuestionSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    is_processed = serializers.BooleanField()

    description = serializers.CharField()
    text = serializers.CharField()
    image = serializers.CharField()
    audio = serializers.CharField()
    video = serializers.CharField()

    answer_description = serializers.CharField()
    answer_text = serializers.CharField()
    answer_image = serializers.CharField()
    answer_audio = serializers.CharField()
    answer_video = serializers.CharField()

    class Meta:
        model = Question


class GameItemSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    type = serializers.CharField()
    is_processed = serializers.BooleanField()
    questions = QuestionSerializer(many=True)

    class Meta:
        model = GameItem


class GameSerializer(serializers.Serializer):
    token = serializers.CharField()
    expired = serializers.DateTimeField()
    connoisseurs_score = serializers.IntegerField()
    viewers_score = serializers.IntegerField()
    cur_item = SerializerMethodField()
    cur_question = SerializerMethodField()
    cur_random_item_idx = serializers.IntegerField(source='cur_random_item')
    cur_item_idx = serializers.IntegerField(source='cur_item')
    cur_question_idx = serializers.IntegerField(source='cur_question')
    state = serializers.CharField()
    items = GameItemSerializer(many=True)
    timer_paused = serializers.BooleanField()
    timer_paused_time = serializers.IntegerField()
    timer_time = serializers.IntegerField()

    def get_cur_item(self, model: Game):
        item = model.items.get(number=model.cur_item) \
            if model.state in (model.STATE_QUESTION_START, model.STATE_QUESTION_DISCUSSION,
                               model.STATE_ANSWER, model.STATE_RIGHT_ANSWER) \
            else None
        return GameItemSerializer().to_representation(item) if item else None

    def get_cur_question(self, model: Game):
        question = model.items.get(number=model.cur_item).questions.get(number=model.cur_question) \
            if model.state in (model.STATE_QUESTION_START, model.STATE_QUESTION_DISCUSSION,
                               model.STATE_ANSWER, model.STATE_RIGHT_ANSWER) \
            else None
        return QuestionSerializer().to_representation(question) if question else None

    class Meta:
        model = Game
