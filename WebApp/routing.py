from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from . import consumers

application = ProtocolTypeRouter({
    "websocket": URLRouter([
        path('transcribe/', consumers.TranscriptionConsumer.as_asgi()),
    ]),
})