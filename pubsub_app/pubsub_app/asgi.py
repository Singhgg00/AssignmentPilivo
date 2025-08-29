import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from pubsub_app.consumer import PubSubConsumer  # adjust if your consumer is elsewhere

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pubsub_app.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws", PubSubConsumer.as_asgi()),  # this is your /ws route
        ])
    ),
})
