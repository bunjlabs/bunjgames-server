from django.urls import path
from django.urls import re_path

from jeopardy import api
from jeopardy.consumers import JeopardyConsumer

urlpatterns = [
    path('v1/create', api.CreateGameAPI.as_view()),
    path('v1/players/register', api.RegisterPlayerAPI.as_view()),
]

websocket_urlpatterns = [
    re_path(r'(?P<token>\w+)$', JeopardyConsumer),
]
