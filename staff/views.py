from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from .serializers import (
    AdminUserSerializer, 
    AdminPropertySerializer,
    AdminNotificationSerializer
)
from .permissions import IsAdminUser
from users.models import User
from properties.models import Property
from notifications.models import Notification

class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response({
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'user_types': User.objects.values('user_type').annotate(count=Count('id'))
        })

    @action(detail=True, methods=['post'])
    def toggle_verification(self, request, pk=None):
        user = self.get_object()
        user.is_verified = not user.is_verified
        user.save()
        return Response({'status': 'success'})

class AdminPropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = AdminPropertySerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        return Response({
            'total_properties': Property.objects.count(),
            'by_type': Property.objects.values('property_type').annotate(count=Count('id')),
            'by_listing': Property.objects.values('listing_type').annotate(count=Count('id'))
        })

class AdminNotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        message = request.data.get('message')
        title = request.data.get('title')
        if not message or not title:
            return Response(
                {'error': 'Message and title are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = [
            Notification(
                recipient=user,
                notification_type='SYSTEM',
                title=title,
                message=message
            ) for user in User.objects.all()
        ]
        Notification.objects.bulk_create(notifications)
        return Response({'status': 'success'})