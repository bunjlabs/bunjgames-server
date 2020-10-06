from django.urls import re_path

from .consumers import WhirligigConsumer

websocket_urlpatterns = [
    re_path(r'v1/ws/(?P<token>\w+)$', WhirligigConsumer),
]
