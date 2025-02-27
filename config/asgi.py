import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from chat.middleware import TokenAuthMiddleware  # Use the new middleware
from chat.routing import websocket_urlpatterns

# Initialize Django ASGI application
django_asgi_app = get_asgi_application()

# Define the ASGI application
application = ProtocolTypeRouter({
    # Django's ASGI application for handling HTTP requests
    "http": django_asgi_app,
    
    # WebSocket handler with Token authentication
    "websocket": AllowedHostsOriginValidator(
        TokenAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})