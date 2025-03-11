from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from .models import Property, PropertyView, SubscriptionPlan, UserSubscription, Transaction
from .serializers import (
    PropertySerializer, DashboardSerializer, SubscriptionPlanSerializer, 
    UserSubscriptionSerializer, TransactionSerializer, InitiatePaymentSerializer
)
from .filters import PropertyFilter
from .utils.paystack import PaystackService
from notifications.models import Notification
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import timedelta

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PropertyFilter
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['price', 'created_at', 'boost_expiry']

    def get_queryset(self):
        queryset = super().get_queryset()
        # Boosted properties appear first
        return queryset.order_by('-boost_expiry', '-created_at')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_subscription'] = self._get_user_subscription()
        return context

    def _get_user_subscription(self):
        if not self.request.user.is_authenticated:
            return None
        try:
            return UserSubscription.objects.filter(
                user=self.request.user,
                is_active=True,
                end_date__gt=timezone.now()
            ).latest('end_date')
        except UserSubscription.DoesNotExist:
            return None

    def _check_view_limit(self, user):
        if not user.is_authenticated:
            return False
        subscription = self._get_user_subscription()
        if subscription and subscription.is_valid():
            if subscription.plan.max_views is None:  # Unlimited views
                return True
            views = PropertyView.objects.filter(user=user, viewed_at__gte=subscription.start_date).count()
            return views < subscription.plan.max_views
        # Free tier: 5 views per month
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        views = PropertyView.objects.filter(user=user, viewed_at__gte=start_of_month).count()
        return views < 5

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user)
        Notification.objects.create(
            recipient=self.request.user,
            message=f"Your property '{instance.title}' has been created.",
            notification_type="PROPERTY_CREATED"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        can_view = self._check_view_limit(request.user)
        
        if not can_view and not request.user.is_authenticated:
            raise PermissionDenied("Please log in to view property details.")
        elif not can_view:
            raise PermissionDenied(
                "You have reached your view limit. Subscribe or use Pay-Per-View to unlock this property."
            )
        
        instance.views += 1
        instance.last_viewed = timezone.now()
        instance.save()
        if request.user.is_authenticated:
            PropertyView.objects.create(user=request.user, property=instance)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='dashboard', url_name='dashboard')
    def dashboard(self, request):
        user = request.user
        if user.user_type not in ['OWNER', 'AGENT']:
            return Response({'error': 'Unauthorized access'}, status=status.HTTP_403_FORBIDDEN)

        stats = {
            'current_properties': Property.objects.filter(owner=user, is_sold=False, is_rented=False).count(),
            'sold_properties': Property.objects.filter(owner=user, is_sold=True).count(),
            'rented_properties': Property.objects.filter(owner=user, is_rented=True).count(),
            'total_views': Property.objects.filter(owner=user).aggregate(Sum('views'))['views__sum'] or 0,
        }
        recently_viewed = Property.objects.filter(Q(owner=user) & Q(last_viewed__isnull=False)).order_by('-last_viewed')[:5]
        serializer = DashboardSerializer({'recently_viewed': recently_viewed, **stats}, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='increment-view', url_name='increment-view')
    def increment_view(self, request, pk=None):
        property = self.get_object()
        property.views += 1
        property.last_viewed = timezone.now()
        property.save()
        if request.user.is_authenticated:
            PropertyView.objects.create(user=request.user, property=property)
        return Response({'status': 'View count updated'})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='initiate-payment', url_name='initiate-payment')
    def initiate_payment(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        paystack = PaystackService()
        callback_url = request.build_absolute_uri('/api/properties/verify-payment/')
        user = request.user
        amount = None
        metadata = {}

        if 'plan_id' in serializer.validated_data:
            # Subscription Payment
            plan = SubscriptionPlan.objects.get(id=serializer.validated_data['plan_id'], is_active=True)
            amount = plan.price
            metadata = {'type': 'SUBSCRIPTION', 'plan_id': plan.id, 'user_id': user.id}
            transaction_type = 'SUBSCRIPTION'
        elif 'property_id' in serializer.validated_data:
            # Pay-Per-View Payment
            property = Property.objects.get(id=serializer.validated_data['property_id'])
            amount = 100  # ₦100 per view
            metadata = {'type': 'PAY_PER_VIEW', 'property_id': property.id, 'user_id': user.id}
            transaction_type = 'PAY_PER_VIEW'
        elif 'boost_duration_days' in serializer.validated_data:
            # Listing Boost Payment
            property = Property.objects.get(id=request.data.get('property_id'), owner=user)
            duration_days = serializer.validated_data['boost_duration_days']
            amount = duration_days * 500  # ₦500 per day
            metadata = {'type': 'BOOST', 'property_id': property.id, 'duration_days': duration_days, 'user_id': user.id}
            transaction_type = 'BOOST'
        else:
            return Response({'error': 'Invalid payment type'}, status=status.HTTP_400_BAD_REQUEST)

        payment_data = paystack.initialize_transaction(
            email=user.email,
            amount=amount,
            callback_url=callback_url,
            metadata=metadata
        )
        
        if payment_data:
            transaction = Transaction.objects.create(
                user=user,
                amount=amount,
                transaction_type=transaction_type,
                reference=payment_data['reference'],
                paystack_reference=payment_data['reference'],
                status='PENDING',
                property=property if 'property_id' in metadata else None
            )
            return Response({
                'authorization_url': payment_data['authorization_url'],
                'reference': payment_data['reference']
            })
        return Response({'error': 'Payment initialization failed'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='verify-payment', url_name='verify-payment')
    def verify_payment(self, request):
        reference = request.GET.get('reference')
        if not reference:
            return Response({'error': 'Reference required'}, status=status.HTTP_400_BAD_REQUEST)
        
        paystack = PaystackService()
        verification = paystack.verify_transaction(reference)
        if not verification or verification['status'] != 'success':
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction = Transaction.objects.get(paystack_reference=reference)
        if transaction.status == 'SUCCESS':
            return Response({'message': 'Payment already verified'})
        
        metadata = verification.get('metadata', {})
        transaction.status = 'SUCCESS'
        
        if metadata['type'] == 'SUBSCRIPTION':
            plan = SubscriptionPlan.objects.get(id=metadata['plan_id'])
            start_date = timezone.now()
            end_date = start_date + timedelta(days=plan.duration_days)
            UserSubscription.objects.filter(user=request.user, is_active=True).update(is_active=False)
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                start_date=start_date,
                end_date=end_date,
                paystack_reference=reference,
                is_active=True
            )
            transaction.subscription = subscription
            Notification.objects.create(
                recipient=request.user,
                message=f"Your {plan.name} subscription is now active.",
                notification_type="SUBSCRIPTION_ACTIVE"
            )
        elif metadata['type'] == 'PAY_PER_VIEW':
            property = Property.objects.get(id=metadata['property_id'])
            transaction.property = property
            PropertyView.objects.create(user=request.user, property=property)
            Notification.objects.create(
                recipient=request.user,
                message=f"You have unlocked details for '{property.title}'.",
                notification_type="PAY_PER_VIEW"
            )
        elif metadata['type'] == 'BOOST':
            property = Property.objects.get(id=metadata['property_id'])
            duration_days = metadata['duration_days']
            property.boost_expiry = timezone.now() + timedelta(days=duration_days)
            property.save()
            transaction.property = property
            Notification.objects.create(
                recipient=request.user,
                message=f"Your listing '{property.title}' has been boosted for {duration_days} days.",
                notification_type="BOOST_ACTIVE"
            )
        
        transaction.save()
        return Response({'message': f'{metadata["type"]} payment verified successfully'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='subscriptions', url_name='subscriptions')
    def list_subscriptions(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)