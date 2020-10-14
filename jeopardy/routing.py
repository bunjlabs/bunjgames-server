from django.urls import re_path

from jeopardy.consumers import JeopardyConsumer

websocket_urlpatterns = [
    re_path(r'v1/ws/(?P<token>\w+)$', JeopardyConsumer),
]
