from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet

# Create a router instance
router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')

# Define urlpatterns
urlpatterns = [
    # Include all router-generated URLs
    path('', include(router.urls)),
]
