from django.utils.functional import cached_property

from common.serializers import TokenSerializer


class TokenContextMixin:
    @cached_property
    def token(self):
        serializer = TokenSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data.get('token')

    def get_serializer_context(self):
        context = dict(token=self.token)
        if hasattr(super(), "get_serializer_context"):
            context.update(super().get_serializer_context())
        return context
