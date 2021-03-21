from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from feud.models import Game, Question, Answer, Team


class TeamSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    strikes = serializers.IntegerField()
    score = serializers.IntegerField()
    final_score = serializers.IntegerField()

    class Meta:
        model = Team


class AnswerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    value = serializers.IntegerField()
    is_opened = serializers.BooleanField()

    class Meta:
        model = Answer


class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    text = serializers.CharField()
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question


class GameSerializer(serializers.Serializer):
    token = serializers.CharField()
    expired = serializers.DateTimeField()
    round = serializers.IntegerField()
    state = serializers.CharField()
    question = QuestionSerializer()
    answerer = SerializerMethodField()
    timer = serializers.IntegerField()
    teams = TeamSerializer(many=True)

    def get_answerer(self, model: Game):
        return model.answerer.id if model.answerer else None

    class Meta:
        model = Game
