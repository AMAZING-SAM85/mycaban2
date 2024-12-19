from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
import re

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = [
            'email',
            'full_name',
            'phone_number',
            'user_type',
            'password',
            'confirm_password'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True},
            'phone_number': {'required': True},
            'user_type': {'required': True}
        }

    def validate_phone_number(self, value):
        if not re.match(r'^\+234\d{10}$', value):
            raise serializers.ValidationError("Phone number must be in the format +234XXXXXXXXXX")
        return value

    def validate_user_type(self, value):
        valid_types = dict(User.USER_TYPE_CHOICES).keys()
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid user type. Must be one of: {', '.join(valid_types)}")
        return value

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists"})
        
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        
        user = User(
            email=validated_data['email'],
            username=validated_data['email'],
            full_name=validated_data['full_name'],
            phone_number=validated_data['phone_number'],
            user_type=validated_data['user_type'],
            is_active=False
        )
        
        user.set_password(validated_data['password'])
        user.save()
        
        return user

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email address")
        return value

class OTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=False)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No pending verification found for this email")

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone_number',
            'user_type',
            'is_verified',
            'rating',
            'date_joined'
        ]
        read_only_fields = ['email', 'date_joined', 'is_verified']