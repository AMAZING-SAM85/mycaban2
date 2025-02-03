from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property
from .serializers import PropertySerializer
from .filters import PropertyFilter
from notifications.models import Notification
from drf_spectacular.utils import extend_schema, OpenApiParameter

class PropertyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing properties.
    Allows read access to everyone, but only authenticated users can create, update, or delete properties.
    """
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at']

    @extend_schema(
        summary="Create a new property",
        description="Creates a new property and associates it with the currently authenticated user.",
        request=PropertySerializer # Add request schema
    )
    def perform_create(self, serializer):
        """
        Create a property and associate it with the current user.
        """
        instance = serializer.save(owner=self.request.user)

        # Optionally, you can add a notification here after property creation:
        Notification.objects.create(
            recipient=self.request.user,
            message=f"Your property '{instance.title}' has been created.",
            notification_type="PROPERTY_CREATED"  # Define notification types
        )

    @extend_schema(summary="List all properties")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create A property")  # Already documented in perform_create, but good to have here too
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve all property")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update a property")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update on a property")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete a property")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)