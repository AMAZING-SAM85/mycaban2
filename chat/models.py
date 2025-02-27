from django.db import models
from users.models import User
from properties.models import Property

class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('DIRECT', 'Direct Message'),
        ('INQUIRY', 'Property Inquiry'),
    )
    
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    property = models.ForeignKey(
        Property, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_rooms'
    )
    
    def __str__(self):
        return f"ChatRoom {self.id} - {self.room_type}"

class ChatRoomMember(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_rooms')
    last_read = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['chat_room', 'user']

class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

class PropertyInquiry(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    )
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inquiries')
    inquirer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_inquiries')
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    chat_room = models.OneToOneField(
        ChatRoom, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='inquiry'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Schedule(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELED', 'Canceled'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    participants = models.ManyToManyField(User, related_name='schedules')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        ordering = ['-start_time']