from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
import re
from django.contrib.auth.password_validation import validate_password
from .models import Rating


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
    


class UserSerializer(serializers.ModelSerializer):
    """Base serializer for user model"""
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'phone_number', 
                 'user_type', 'is_verified', 'rating', 'date_joined')
        read_only_fields = ('id', 'is_verified', 'date_joined')

class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('full_name', 'phone_number', 'current_password', 'new_password')

    def validate(self, data):
        if 'new_password' in data and not data.get('current_password'):
            raise serializers.ValidationError(
                {"current_password": "Current password is required to set new password"}
            )
        
        if 'new_password' in data:
            validate_password(data['new_password'])
            
        return data

    def update(self, instance, validated_data):
        current_password = validated_data.pop('current_password', None)
        new_password = validated_data.pop('new_password', None)

        if current_password and new_password:
            if not instance.check_password(current_password):
                raise serializers.ValidationError(
                    {"current_password": "Wrong password"}
                )
            instance.set_password(new_password)

        return super().update(instance, validated_data)

class UserDetailSerializer(UserSerializer):
    """Detailed user serializer including more fields"""
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_active', 'is_staff')

class UserListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing users"""
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'user_type', 'rating')


class RatingSerializer(serializers.ModelSerializer):
    rater_name = serializers.CharField(source='rater.full_name', read_only=True)
    rater_type = serializers.CharField(source='rater.user_type', read_only=True)

    class Meta:
        model = Rating
        fields = ('id', 'score', 'review', 'created_at', 
                 'rater', 'rater_name', 'rater_type', 'rated_user')
        read_only_fields = ('rater', 'created_at')

    def validate(self, data):
        request = self.context['request']
        rater = request.user
        rated_user = data['rated_user']

        # Prevent self-rating
        if rater == rated_user:
            raise serializers.ValidationError(
                "You cannot rate yourself."
            )

        # Add any business logic for who can rate whom
        # For example, only allow rating after a transaction
        # if not Transaction.objects.filter(buyer=rater, seller=rated_user).exists():
        #     raise serializers.ValidationError(
        #         "You can only rate users you've had transactions with."
        #     )

        return data

    def create(self, validated_data):
        validated_data['rater'] = self.context['request'].user
        return super().create(validated_data)


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'receive_email_notifications',
            'allow_listing_updates',
            'message_notifications',
            'review_notifications',
            'viewing_notifications',
            'schedule_reminders',
            'profile_visible',
            'listings_private',
            'login_alerts'
        ]

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        validate_password(data['new_password'])
        return data

class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=False)

class GovernmentIDSerializer(serializers.Serializer):
    document = serializers.FileField(required=True)
    document_type = serializers.ChoiceField(choices=[
        ('NIN', 'National Identity Number'),
        ('DRIVER_LICENSE', 'Driver License'),
        ('INTERNATIONAL_PASSPORT', 'International Passport')
    ])