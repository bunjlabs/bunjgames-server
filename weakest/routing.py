from django.urls import re_path

from weakest.consumers import WeakestConsumer

websocket_urlpatterns = [
    re_path(r'(?P<token>\w+)$', WeakestConsumer),
]
