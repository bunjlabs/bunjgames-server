from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

import jeopardy.urls
import weakest.urls
import whirligig.urls
import feud.urls

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('whirligig/ws/', URLRouter(whirligig.urls.websocket_urlpatterns)),
        path('jeopardy/ws/', URLRouter(jeopardy.urls.websocket_urlpatterns)),
        path('weakest/ws/', URLRouter(weakest.urls.websocket_urlpatterns)),
        path('feud/ws/', URLRouter(feud.urls.websocket_urlpatterns)),
    ]),
})
