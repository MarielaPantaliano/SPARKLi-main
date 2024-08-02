import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import WebApp.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SPARKLi.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            WebApp.routing.websocket_urlpatterns
        )
    ),
})
