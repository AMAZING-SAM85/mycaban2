from rest_framework import serializers
from .utils.appwrite import AppwriteHelper
from .models import Property, PropertyAmenity, PropertyMedia
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
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['owner', 'latitude', 'longitude', 'formatted_address', 'place_id']

    def get_location_details(self, obj):
        """Return formatted location details."""
        return {
            'address': obj.formatted_address or obj.location,
            'coordinates': {
                'lat': float(obj.latitude) if obj.latitude else None,
                'lng': float(obj.longitude) if obj.longitude else None
            },
            'place_id': obj.place_id
        }

    def _handle_location_data(self, location: str) -> dict:
        """Handle geocoding and return location data."""
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
        
        # Handle geocoding
        location_data = self._handle_location_data(validated_data['location'])
        validated_data.update(location_data)
        
        # Create property instance
        property_instance = Property.objects.create(**validated_data)
        
        # Handle amenities
        for amenity in amenities_data:
            PropertyAmenity.objects.create(property=property_instance, **amenity)
        
        # Handle media files
        appwrite_helper = AppwriteHelper()
        for media_file in media_files:
            file_url = appwrite_helper.upload_file(
                file=media_file,
                user_id=str(property_instance.owner.id)
            )
            
            # Determine media type based on file extension
            media_type = 'VIDEO' if media_file.name.lower().endswith(('.mp4', '.mov', '.avi')) else 'IMAGE'
            
            PropertyMedia.objects.create(
                property=property_instance,
                media_type=media_type,
                file_url=file_url
            )
        
        return property_instance

    def update(self, instance, validated_data):
        # Update geocoding data if location has changed
        if 'location' in validated_data and validated_data['location'] != instance.location:
            location_data = self._handle_location_data(validated_data['location'])
            validated_data.update(location_data)

        # Handle existing amenities and media updates if needed
        amenities_data = validated_data.pop('amenities', None)
        if amenities_data is not None:
            instance.amenities.all().delete()
            for amenity in amenities_data:
                PropertyAmenity.objects.create(property=instance, **amenity)

        # Update the instance with the remaining validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance