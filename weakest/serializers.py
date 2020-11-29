from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from weakest.models import Game, Question, Player


class PlayerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    is_weak = serializers.BooleanField()
    weak = SerializerMethodField()
    right_answers = serializers.IntegerField()
    bank_income = serializers.IntegerField()

    def get_weak(self, model: Player):
        return model.weak.id if model.weak else None

    class Meta:
        model = Player


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()

    class Meta:
        model = Question


class GameSerializer(serializers.Serializer):
    token = serializers.CharField()
    expired = serializers.DateTimeField()
    score_multiplier = serializers.IntegerField()
    score = serializers.IntegerField()
    bank = serializers.IntegerField()
    tmp_score = serializers.IntegerField()
    state = serializers.CharField()
    round = serializers.IntegerField()
    question = QuestionSerializer()
    answerer = SerializerMethodField()
    weakest = SerializerMethodField()
    strongest = SerializerMethodField()
    timer = serializers.IntegerField()
    players = PlayerSerializer(many=True)

    def get_answerer(self, model: Game):
        return model.answerer.id if model.answerer else None

    def get_weakest(self, model: Game):
        return model.weakest.id if model.weakest else None

    def get_strongest(self, model: Game):
        return model.strongest.id if model.strongest else None

    class Meta:
        model = Game
