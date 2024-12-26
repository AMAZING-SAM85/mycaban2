from django.db import models
from users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('PROPERTY_CREATED', 'New Property Listed'),
        ('PROPERTY_UPDATED', 'Property Updated'),
        ('PROPERTY_DELETED', 'Property Removed'),
        ('SYSTEM', 'System Notification')
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_property_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)