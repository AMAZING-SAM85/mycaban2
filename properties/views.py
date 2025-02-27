from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyView
from django.db.models import Sum, Q
from .serializers import DashboardSerializer, PropertySerializer
from .filters import PropertyFilter
from notifications.models import Notification
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils import timezone

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
        request=PropertySerializer
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
            notification_type="PROPERTY_CREATED"
        )

    @extend_schema(summary="List all properties")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create A property")
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
    
    @action(detail=False, methods=['get'], url_path='dashboard', url_name='dashboard')
    def dashboard(self, request):
        user = request.user
        
        # Authorization check
        if user.user_type not in ['OWNER', 'AGENT']:
            return Response(
                {'error': 'Unauthorized access'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Dashboard statistics
        stats = {
            'current_properties': Property.objects.filter(owner=user, is_sold=False, is_rented=False).count(),
            'sold_properties': Property.objects.filter(owner=user, is_sold=True).count(),
            'rented_properties': Property.objects.filter(owner=user, is_rented=True).count(),
            'total_views': Property.objects.filter(owner=user).aggregate(Sum('views'))['views__sum'] or 0,
        }

        # Recently viewed properties (last 5 viewed)
        recently_viewed = Property.objects.filter(
            Q(owner=user) & Q(last_viewed__isnull=False)
        ).order_by('-last_viewed')[:5]

        serializer = DashboardSerializer({
            **stats,
            'recently_viewed': recently_viewed
        })

        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='increment-view', url_name='increment-view')
    def increment_view(self, request, pk=None):
        property = self.get_object()
        property.views += 1
        property.last_viewed = timezone.now()
        property.save()
        
        # Record individual view
        PropertyView.objects.create(
            user=request.user,
            property=property
        )
        
        return Response({'status': 'View count updated'})