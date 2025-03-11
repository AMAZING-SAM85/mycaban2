from rest_framework import serializers
from .utils.appwrite import AppwriteHelper
from .models import Property, PropertyAmenity, PropertyMedia, PropertyView, SubscriptionPlan, UserSubscription, Transaction
from .utils.geocoding import GeocodingService
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'full_name', 'email', 'rating']

class PropertyAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyAmenity
        fields = ['id', 'name']

class PropertyMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = ['id', 'media_type', 'file_url', 'created_at']

class PropertySerializer(serializers.ModelSerializer):
    amenities = PropertyAmenitySerializer(many=True, required=False)
    media = PropertyMediaSerializer(many=True, read_only=True)
    media_files = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False
    )
    owner = UserSerializer(read_only=True)
    location_details = serializers.SerializerMethodField()
    is_boosted = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['owner', 'formatted_address', 'place_id', 'views', 'boost_expiry']

    def get_location_details(self, obj):
        return {
            'address': obj.formatted_address or obj.location,
            'coordinates': {
                'lat': float(obj.latitude) if obj.latitude else None,
                'lng': float(obj.longitude) if obj.longitude else None
            },
            'place_id': obj.place_id
        }

    def get_is_boosted(self, obj):
        return obj.is_boosted()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user_subscription = self.context.get('user_subscription')
        request = self.context.get('request')
        
        if not request.user.is_authenticated:
            # Non-authenticated users see only basic fields
            limited_fields = ['id', 'title', 'price', 'location', 'property_type', 'listing_type', 'is_boosted']
            return {key: representation[key] for key in limited_fields}
        
        if not user_subscription or not user_subscription.is_valid():
            # Free tier: Limit fields
            limited_fields = ['id', 'title', 'price', 'location', 'property_type', 'listing_type', 'is_boosted']
            return {key: representation[key] for key in limited_fields}
        
        # Check plan-specific restrictions
        if instance.is_exclusive and not user_subscription.plan.exclusive_access:
            return {'error': 'This is an exclusive listing. Upgrade to Premium Plan to view.'}
        
        return representation

    def _handle_location_data(self, location: str, latitude=None, longitude=None) -> dict:
        if latitude and longitude:
            return {
                'latitude': latitude,
                'longitude': longitude,
                'formatted_address': location,
                'place_id': None
            }
        geocoding_service = GeocodingService()
        location_details = geocoding_service.get_location_details(location)
        if location_details:
            return {
                'latitude': location_details['latitude'],
                'longitude': location_details['longitude'],
                'formatted_address': location_details['formatted_address'],
                'place_id': location_details['place_id']
            }
        return {}

    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        amenities_data = validated_data.pop('amenities', [])
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)
        location_data = self._handle_location_data(validated_data['location'], latitude, longitude)
        validated_data.update(location_data)
        
        property_instance = Property.objects.create(owner=self.context['request'].user, **validated_data)
        
        for amenity in amenities_data:
            PropertyAmenity.objects.create(property=property_instance, **amenity)
        
        appwrite_helper = AppwriteHelper()
        for media_file in media_files:
            file_url = appwrite_helper.upload_file(file=media_file, user_id=str(property_instance.owner.id))
            media_type = 'VIDEO' if media_file.name.lower().endswith(('.mp4', '.mov', '.avi')) else 'IMAGE'
            PropertyMedia.objects.create(property=property_instance, media_type=media_type, file_url=file_url)
        
        return property_instance

    def update(self, instance, validated_data):
        if 'location' in validated_data or 'latitude' in validated_data or 'longitude' in validated_data:
            latitude = validated_data.pop('latitude', instance.latitude)
            longitude = validated_data.pop('longitude', instance.longitude)
            location_data = self._handle_location_data(validated_data.get('location', instance.location), latitude, longitude)
            validated_data.update(location_data)

        amenities_data = validated_data.pop('amenities', None)
        if amenities_data is not None:
            instance.amenities.all().delete()
            for amenity in amenities_data:
                PropertyAmenity.objects.create(property=instance, **amenity)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'plan_type', 'price', 'duration_days', 'description', 'max_views', 'exclusive_access', 'listing_management']

class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date', 'is_active']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'transaction_type', 'reference', 'status', 'created_at']

class DashboardSerializer(serializers.Serializer):
    current_properties = serializers.IntegerField()
    sold_properties = serializers.IntegerField()
    rented_properties = serializers.IntegerField()
    total_views = serializers.IntegerField()
    recently_viewed = PropertySerializer(many=True)
    recent_views = serializers.SerializerMethodField()

    def get_recent_views(self, obj):
        request = self.context.get('request')
        recent_views = PropertyView.objects.filter(
            user=request.user
        ).select_related('property').order_by('-viewed_at')[:5]
        return PropertySerializer(
            [view.property for view in recent_views], 
            many=True,
            context={'request': request}
        ).data

class InitiatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=False)
    property_id = serializers.IntegerField(required=False)
    boost_duration_days = serializers.IntegerField(required=False, min_value=1)