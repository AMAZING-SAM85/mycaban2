from rest_framework import serializers
from users.models import User
from properties.models import Property, PropertyMedia, PropertyAmenity
from notifications.models import Notification

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class AdminPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = '__all__'

class AdminNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'