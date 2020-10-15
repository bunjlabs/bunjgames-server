from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

import jeopardy.routing
import whirligig.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/whirligig/', URLRouter(whirligig.routing.websocket_urlpatterns)),
        path('ws/jeopardy/', URLRouter(jeopardy.routing.websocket_urlpatterns)),
    ]),
})
