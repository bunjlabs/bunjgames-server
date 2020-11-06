from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

import jeopardy.routing
import weakest.routing
import whirligig.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('whirligig/ws/', URLRouter(whirligig.routing.websocket_urlpatterns)),
        path('jeopardy/ws/', URLRouter(jeopardy.routing.websocket_urlpatterns)),
        path('weakest/ws/', URLRouter(weakest.routing.websocket_urlpatterns)),
    ]),
})
