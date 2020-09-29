from channels.routing import ProtocolTypeRouter, URLRouter

import whirligig.routing

application = ProtocolTypeRouter({
    'websocket': URLRouter(
        whirligig.routing.websocket_urlpatterns
    ),
})
