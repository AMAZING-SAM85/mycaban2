from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, PropertyInquiryViewSet, ScheduleViewSet

router = DefaultRouter()
router.register(r'chatrooms', ChatRoomViewSet, basename='chatroom')
router.register(r'inquiries', PropertyInquiryViewSet, basename='inquiry')
router.register(r'schedules', ScheduleViewSet, basename='schedule')


urlpatterns = [
    path('', include(router.urls)),
]