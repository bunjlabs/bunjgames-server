from rest_framework import serializers


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(allow_null=True, required=False)

    def __init__(self, *args, **kwargs):
        serializers.Serializer.__init__(self, *args, **kwargs)
