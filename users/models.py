from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from .managers import CustomUserManager

class User(AbstractUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('OWNER', 'Property Owner'),
        ('AGENT', 'Real Estate Agent'),
        ('BUYER', 'Buyer/Renter'),
    )
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=15, 
        validators=[RegexValidator(
            regex=r'^\+?234\d{10}$', 
            message='Phone number must be in the format +234XXXXXXXXXX'
        )]
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    is_verified = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'phone_number']
    
    def __str__(self):
        return self.username

    def is_otp_valid(self):
        """
        Check if the OTP is still valid (within 4 minutes)
        """
        if not self.otp or not self.otp_created_at:
            return False
        
        time_elapsed = timezone.now() - self.otp_created_at
        return time_elapsed.total_seconds() <= 240  # 4 minutes = 240 seconds