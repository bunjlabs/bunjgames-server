from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from jeopardy.models import Game, Question, Theme, Player


class PlayerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    balance = serializers.IntegerField()
    final_bet = serializers.IntegerField()
    final_answer = serializers.CharField()

    class Meta:
        model = Player


class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    custom_theme = serializers.CharField()

    text = serializers.CharField()
    image = serializers.CharField()
    audio = serializers.CharField()
    video = serializers.CharField()

    answer_text = serializers.CharField()
    answer_image = serializers.CharField()
    answer_audio = serializers.CharField()
    answer_video = serializers.CharField()

    value = serializers.IntegerField()
    answer = serializers.CharField()
    comment = serializers.CharField()
    type = serializers.CharField()
    is_processed = serializers.BooleanField()

    class Meta:
        model = Question


class ThemeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    is_removed = serializers.BooleanField()
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Theme


class GameSerializer(serializers.Serializer):
    token = serializers.CharField()
    expired = serializers.DateTimeField()
    round = serializers.IntegerField()
    rounds_count = serializers.IntegerField(source='last_round')
    is_final_round = SerializerMethodField()
    state = serializers.CharField()
    question = QuestionSerializer()
    themes = SerializerMethodField()
    players = PlayerSerializer(many=True)
    answerer = SerializerMethodField()
    name = serializers.ReadOnlyField(default='jeopardy')

    def get_themes(self, model: Game):
        return ThemeSerializer(many=True).to_representation(model.get_themes())

    def get_is_final_round(self, model: Game):
        return model.is_final_round()

    def get_answerer(self, model: Game):
        return model.answerer.id if model.answerer else None

    class Meta:
        model = Game
