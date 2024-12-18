from rest_framework import serializers

from .utils.appwrite import AppwriteHelper
from .models import Property, PropertyAmenity, PropertyMedia

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
    
    class Meta:
        model = Property
        fields = '__all__'
        read_only_fields = ['owner']
    
    def create(self, validated_data):
        media_files = validated_data.pop('media_files', [])
        amenities_data = validated_data.pop('amenities', [])
        
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