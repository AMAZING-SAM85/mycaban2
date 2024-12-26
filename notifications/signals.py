from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from properties.models import Property
from users.models import User
from .models import Notification

@receiver(post_save, sender=Property)
def handle_property_save(sender, instance, created, **kwargs):
    users = User.objects.filter(is_active=True)
    
    notification_type = 'PROPERTY_CREATED' if created else 'PROPERTY_UPDATED'
    message = f'New property listed: {instance.title}' if created else f'Property updated: {instance.title}'
    
    for user in users:
        Notification.objects.create(
            recipient=user,
            notification_type=notification_type,
            title=instance.title,
            message=message,
            related_property_id=instance.id
        )

@receiver(post_delete, sender=Property)
def handle_property_delete(sender, instance, **kwargs):
    users = User.objects.filter(is_active=True)
    
    for user in users:
        Notification.objects.create(
            recipient=user,
            notification_type='PROPERTY_DELETED',
            title=instance.title,
            message=f'Property removed: {instance.title}'
        )