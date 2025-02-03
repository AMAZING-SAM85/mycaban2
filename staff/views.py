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
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users (admin access).
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get user statistics",
        description="Retrieves various statistics about users.",
        responses={200: inline_serializer(
            'UserStatsSerializer',
            fields={
                'total_users': serializers.IntegerField(),
                'verified_users': serializers.IntegerField(),
                'user_types': serializers.ListField()  # Adjust as needed
            }
        )}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get user statistics.
        """
        return Response({
            'total_users': User.objects.count(),
            'verified_users': User.objects.filter(is_verified=True).count(),
            'user_types': User.objects.values('user_type').annotate(count=Count('id'))
        })

    @extend_schema(
        summary="Toggle user verification",
        description="Toggles the verification status of a user.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the user to toggle verification."
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def toggle_verification(self, request, pk=None):
        """
        Toggle user verification status.
        """
        user = self.get_object()
        user.is_verified = not user.is_verified
        user.save()
        return Response({'status': 'success'})


    @extend_schema(summary="List users (admin)")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create user (admin)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve user (admin)")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update user (admin)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update user (admin)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete user (admin)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



class AdminPropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing properties (admin access).
    """
    queryset = Property.objects.all()
    serializer_class = AdminPropertySerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Get property statistics",
        description="Retrieves various statistics about properties.",
        responses={200: inline_serializer(
            'PropertyStatsSerializer',
            fields={
                'total_properties': serializers.IntegerField(),
                'by_type': serializers.ListField(),  # Adjust as needed
                'by_listing': serializers.ListField() # Adjust as needed
            }
        )}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get property statistics.
        """
        return Response({
            'total_properties': Property.objects.count(),
            'by_type': Property.objects.values('property_type').annotate(count=Count('id')),
            'by_listing': Property.objects.values('listing_type').annotate(count=Count('id'))
        })

    @extend_schema(summary="List properties (admin)")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create property (admin)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve property (admin)")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update property (admin)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update property (admin)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete property (admin)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



class AdminNotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications (admin access).
    """
    queryset = Notification.objects.all()
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Broadcast a notification to all users",
        description="Sends a notification to all users in the system.",
        request=inline_serializer(
            'BroadcastSerializer',
            fields={
                'message': serializers.CharField(),
                'title': serializers.CharField()
            }
        )
    )
    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        """
        Broadcast a notification.
        """
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

    @extend_schema(summary="List notifications (admin)")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create notification (admin)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve notification (admin)")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update notification (admin)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update notification (admin)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete notification (admin)")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)