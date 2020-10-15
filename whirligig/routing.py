from django.urls import re_path

from .consumers import WhirligigConsumer

websocket_urlpatterns = [
    re_path(r'(?P<token>\w+)$', WhirligigConsumer),
]
