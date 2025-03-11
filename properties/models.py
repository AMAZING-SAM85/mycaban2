from django.db import models
from django.utils import timezone
from users.models import User
from datetime import timedelta

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('HOUSE', 'House'),
        ('APARTMENT', 'Apartment'),
        ('LAND', 'Land'),
        ('COMMERCIAL', 'Commercial'),
    )
    
    LISTING_TYPE_CHOICES = (
        ('SALE', 'For Sale'),
        ('RENT', 'For Rent'),
        ('SHORTLET', 'Shortlet'),
    )
    
    FURNISHING_CHOICES = (
        ('FULLY', 'Fully Furnished'),
        ('SEMI', 'Semi-Furnished'),
        ('NONE', 'Unfurnished'),
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    size = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    formatted_address = models.CharField(max_length=255, blank=True, null=True)
    place_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    is_sold = models.BooleanField(default=False)
    is_rented = models.BooleanField(default=False)
    last_viewed = models.DateTimeField(null=True, blank=True)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    toilets = models.PositiveIntegerField(default=1)
    year_built = models.PositiveIntegerField(null=True, blank=True)
    has_air_conditioner = models.BooleanField(default=False)
    furnishing_type = models.CharField(max_length=20, choices=FURNISHING_CHOICES, default='NONE')
    power_supply = models.BooleanField(default=False)
    water_supply = models.BooleanField(default=False)
    is_exclusive = models.BooleanField(default=False)  # For Premium Plan exclusive listings
    boost_expiry = models.DateTimeField(null=True, blank=True)  # For Listing Boosts

    def __str__(self):
        return self.title

    def is_boosted(self):
        return self.boost_expiry and timezone.now() < self.boost_expiry

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, related_name='amenities', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name_plural = 'Property Amenities'

class PropertyMedia(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    )
    
    property = models.ForeignKey(Property, related_name='media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    file_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

class PropertyView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

class SubscriptionPlan(models.Model):
    PLAN_TYPES = (
        ('BASIC', 'Basic Plan'),
        ('PREMIUM', 'Premium Plan'),
        ('AGENT', 'Agent Plan'),
    )
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # In Naira
    duration_days = models.PositiveIntegerField()  # Subscription duration in days
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    max_views = models.PositiveIntegerField(null=True, blank=True)  # None for unlimited
    exclusive_access = models.BooleanField(default=False)  # For Premium Plan
    listing_management = models.BooleanField(default=False)  # For Agent Plan

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    paystack_reference = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.plan.name}"

    def is_valid(self):
        return self.is_active and timezone.now() < self.end_date

class Transaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    )
    TRANSACTION_TYPES = (
        ('SUBSCRIPTION', 'Subscription'),
        ('PAY_PER_VIEW', 'Pay Per View'),
        ('BOOST', 'Listing Boost'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=255, unique=True)
    paystack_reference = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    subscription = models.ForeignKey(UserSubscription, null=True, blank=True, on_delete=models.SET_NULL)
    property = models.ForeignKey(Property, null=True, blank=True, on_delete=models.SET_NULL)  # For PPV or Boost

    def __str__(self):
        return f"{self.user} - {self.reference}"