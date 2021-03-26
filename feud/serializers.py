from django.db.models import Prefetch
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
    final_questions = SerializerMethodField()
    timer = serializers.IntegerField()
    teams = TeamSerializer(many=True)

    def get_answerer(self, model: Game):
        return model.answerer.id if model.answerer else None

    def get_final_questions(self, model: Game):
        return QuestionSerializer(model.questions.filter(is_final=True).prefetch_related(
            Prefetch('answers', queryset=Answer.objects.filter(is_opened=True))
        ), many=True).data if model.state == model.STATE_FINAL_QUESTIONS_REVEAL else None

    class Meta:
        model = Game
