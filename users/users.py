from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, 
    UserUpdateSerializer,
    UserDetailSerializer,
    UserListSerializer
)
from .permissions import IsOwnerOrAdmin

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_type', 'is_verified']
    search_fields = ['email', 'full_name', 'phone_number']
    ordering_fields = ['date_joined', 'rating']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Get current user profile",
        description="Retrieve the profile of the currently authenticated user"
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserDetailSerializer
    )
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        summary="Update current user profile",
        description="Update the profile of the currently authenticated user"
    )
    @action(
        detail=False,
        methods=['put', 'patch'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserUpdateSerializer
    )
    def update_me(self, request):
        """Update current user's profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=request.method == 'PATCH'
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="List users by type",
        parameters=[
            OpenApiParameter(
                name="user_type",
                type=str,
                required=True,
                enum=['OWNER', 'AGENT', 'BUYER']
            )
        ]
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserListSerializer
    )
    def by_type(self, request):
        """List users filtered by user_type"""
        user_type = request.query_params.get('user_type')
        if not user_type:
            return Response(
                {'error': 'user_type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(user_type=user_type)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get top rated users",
        parameters=[
            OpenApiParameter(
                name="limit",
                type=int,
                required=False,
                default=10
            )
        ]
    )
    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserListSerializer
    )
    def top_rated(self, request):
        """Get top rated users"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().exclude(
            rating__isnull=True
        ).order_by('-rating')[:limit]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)