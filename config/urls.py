from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/properties/', include('properties.urls')),
    path('api/notifications/', include("notifications.urls")),
    path('api/admin/', include('staff.urls')),
    path('api/chat/', include('chat.urls')),
    path(
        "api/schema/", SpectacularAPIView.as_view(), name="schema"
    ),  # JSON Schema generation
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),  # Swagger UI
    path(
        "api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),  # Redoc UI
]
