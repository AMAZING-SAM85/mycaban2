from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get notifications for the currently authenticated user, ordered by creation time.
        """
        return Notification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

    @extend_schema(
        summary="Mark all notifications as read",
        description="Marks all unread notifications for the current user as read."
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all notifications as read.
        """
        self.get_queryset().update(is_read=True)
        return Response(status=status.HTTP_200_OK)

    @extend_schema(
        summary="Mark a single notification as read",
        description="Marks a specific notification as read, given its ID.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the notification to mark as read."
            )
        ]
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark a single notification as read.
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(status=status.HTTP_200_OK)

    @extend_schema(summary="List notifications")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create notification")  # If you allow creation via API
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve notification")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update notification")  # If you allow updates
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update notification") # If you allow partial updates
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete notification")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)