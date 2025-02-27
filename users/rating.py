from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count, Q
from .models import Rating
from .serializers import RatingSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, inline_serializer
from rest_framework import serializers

class RatingViewSet(viewsets.ModelViewSet):
    """
    viewset for managing user ratings
    ViewSet for managing user ratings.
    """
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
 
    def get_queryset(self):
        """
        Get all ratings (you can add custom filtering here if needed).
        """
        return Rating.objects.all()

    @extend_schema(
        summary="Create a new rating",
        description="Creates a new rating. The currently authenticated user will be the rater.",
        request=RatingSerializer  # Add request schema
    )
    def perform_create(self, serializer):
        """
        Create a rating and set the rater to the current user.
        """
        serializer.save(rater=self.request.user)

    @extend_schema(
        summary="Get ratings received by the current user",
        description="Retrieves all ratings received by the currently authenticated user and calculates statistics.",
        responses={
            200: inline_serializer(
                'ReceivedRatingsResponseSerializer',
                fields={
                    'ratings': RatingSerializer(many=True),
                    'statistics': inline_serializer(
                        'RatingStatsSerializer',
                        fields={
                            'average': serializers.FloatField(),
                            'total_count': serializers.IntegerField(),
                            'five_star': serializers.IntegerField(),
                            'four_star': serializers.IntegerField(),
                            'three_star': serializers.IntegerField(),
                            'two_star': serializers.IntegerField(),
                            'one_star': serializers.IntegerField()
                        }
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def my_ratings_received(self, request):
        """
        Get ratings received by the current user and calculate statistics.
        """
        ratings = Rating.objects.filter(rated_user=request.user)
        serializer = self.get_serializer(ratings, many=True)
        
        # Calculate statistics
        stats = ratings.aggregate(
            average=Avg('score'),
            total_count=Count('id'),
            five_star=Count('id', filter=Q(score=5)),
            four_star=Count('id', filter=Q(score=4)),
            three_star=Count('id', filter=Q(score=3)),
            two_star=Count('id', filter=Q(score=2)),
            one_star=Count('id', filter=Q(score=1))
        )
        
        return Response({
            'ratings': serializer.data,
            'statistics': stats
        })

    @extend_schema(
        summary="Get ratings given by the current user",
        description="Retrieves all ratings given by the currently authenticated user."
    )
    @action(detail=False, methods=['get'])
    def my_ratings_given(self, request):
        """
        Get ratings given by the current user.
        """
        ratings = Rating.objects.filter(rater=request.user)
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Update a rating",
        description="Updates a rating if it belongs to the currently authenticated user.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the rating to update."
            )
        ],
        request=RatingSerializer # Add request schema
    )
    def update(self, request, *args, **kwargs):
        """
        Update a rating (only if owned by the current user).
        """
        instance = self.get_object()
        if instance.rater != request.user:
            return Response(
                {'error': 'You can only modify your own ratings'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a rating",
        description="Deletes a rating if it belongs to the currently authenticated user.",
        parameters=[
            OpenApiParameter(
                name="pk",
                type=int,
                location=OpenApiParameter.PATH,
                description="ID of the rating to delete."
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a rating (only if owned by the current user).
        """
        instance = self.get_object()
        if instance.rater != request.user:
            return Response(
                {'error': 'You can only delete your own ratings'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @extend_schema(summary="List ratings")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create rating")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve rating")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Partial update rating")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)