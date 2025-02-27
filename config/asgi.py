
import django
django.setup()


from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.middleware import WebSocketAuthMiddleware
from chat.routing import websocket_urlpatterns

# Initialize the Django ASGI application.
django_asgi_app = get_asgi_application()

# Build the ProtocolTypeRouter for handling both HTTP and WebSocket connections.
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        WebSocketAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
