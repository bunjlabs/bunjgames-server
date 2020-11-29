from django.urls import path
from django.urls import re_path

from whirligig import api
from whirligig.consumers import WhirligigConsumer

urlpatterns = [
    path('v1/create', api.CreateGameAPI.as_view(), name='create_game'),
]

websocket_urlpatterns = [
    re_path(r'(?P<token>\w+)$', WhirligigConsumer),
]
