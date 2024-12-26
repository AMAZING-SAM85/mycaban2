from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AdminUserViewSet,
    AdminPropertyViewSet,
    AdminNotificationViewSet
)

router = DefaultRouter()
router.register('users', AdminUserViewSet)
router.register('properties', AdminPropertyViewSet)
router.register('notifications', AdminNotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]