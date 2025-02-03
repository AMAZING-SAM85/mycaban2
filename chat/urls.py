from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, PropertyInquiryViewSet

router = DefaultRouter()
router.register(r'chatrooms', ChatRoomViewSet, basename='chatroom')
router.register(r'inquiries', PropertyInquiryViewSet, basename='inquiry')

urlpatterns = [
    path('', include(router.urls)),
]