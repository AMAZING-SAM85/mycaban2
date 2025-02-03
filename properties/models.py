from django.db import models
from users.models import User

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