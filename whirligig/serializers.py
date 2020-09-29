from rest_framework import serializers

from whirligig.models import Game, GameItem, Question


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(allow_null=True, required=False)

    def __init__(self, *args, **kwargs):
        serializers.Serializer.__init__(self, *args, **kwargs)


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
    cur_item = serializers.IntegerField()
    cur_question = serializers.IntegerField()
    state = serializers.CharField()
    items = GameItemSerializer(many=True)

    class Meta:
        model = Game
