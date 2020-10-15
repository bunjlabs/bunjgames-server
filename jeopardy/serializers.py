from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

from jeopardy.models import Game, Question, Category, Player


class PlayerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    balance = serializers.IntegerField()
    final_bet = serializers.IntegerField()
    final_answer = serializers.CharField()

    class Meta:
        model = Player


class QuestionSerializer(serializers.Serializer):
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


class CategorySerializer(serializers.Serializer):
    name = ''
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Category


class GameSerializer(serializers.Serializer):
    token = serializers.CharField()
    expired = serializers.DateTimeField()
    round = serializers.IntegerField()
    is_final_round = SerializerMethodField()
    state = serializers.CharField()
    question = QuestionSerializer()
    categories = SerializerMethodField()
    players = PlayerSerializer(many=True)
    button_won_by = serializers.IntegerField(source="button_won_by.id")

    def get_categories(self, model: Game):
        return CategorySerializer(many=True).to_representation(model.get_categories())

    def get_is_final_round(self, model: Game):
        return model.is_final_round()

    class Meta:
        model = Game