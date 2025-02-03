from rest_framework import serializers
from .models import ChatRoom, Message, PropertyInquiry, ChatRoomMember
from users.serializers import UserProfileSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at', 'is_read']
        read_only_fields = ['is_read']

class ChatRoomMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = ChatRoomMember
        fields = ['id', 'user', 'last_read', 'joined_at']

class ChatRoomSerializer(serializers.ModelSerializer):
    members = ChatRoomMemberSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'room_type', 'created_at', 'members', 'last_message', 'unread_count', 'property']
    
    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return MessageSerializer(last_message).data
        return None
    
    def get_unread_count(self, obj):
        user = self.context['request'].user
        last_read = ChatRoomMember.objects.filter(
            chat_room=obj, 
            user=user
        ).first()
        
        if last_read and last_read.last_read:
            return obj.messages.filter(
                created_at__gt=last_read.last_read
            ).exclude(sender=user).count()
        return obj.messages.exclude(sender=user).count()

class PropertyInquirySerializer(serializers.ModelSerializer):
    inquirer = UserProfileSerializer(read_only=True)
    chat_room = ChatRoomSerializer(read_only=True)
    
    class Meta:
        model = PropertyInquiry
        fields = [
            'id', 'property', 'inquirer', 'subject', 'message',
            'status', 'chat_room', 'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'chat_room']