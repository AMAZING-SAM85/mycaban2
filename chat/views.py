from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import ChatRoom, ChatRoomMember, Message, PropertyInquiry
from .serializers import (
    ChatRoomSerializer,
    MessageSerializer,
    PropertyInquirySerializer
)

class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatRoom.objects.filter(
            members__user=self.request.user
        ).distinct()
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        chat_room = self.get_object()
        messages = chat_room.messages.all()
        serializer = MessageSerializer(messages, many=True)
        
        # Mark messages as read
        messages.filter(
            ~Q(sender=request.user),
            is_read=False
        ).update(is_read=True)
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        chat_room = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'Message content is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = Message.objects.create(
            chat_room=chat_room,
            sender=request.user,
            content=content
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data)

class PropertyInquiryViewSet(viewsets.ModelViewSet):
    serializer_class = PropertyInquirySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['OWNER', 'AGENT']:
            return PropertyInquiry.objects.filter(
                property__owner=user
            )
        return PropertyInquiry.objects.filter(
            inquirer=user
        )
    
    def perform_create(self, serializer):
        inquiry = serializer.save(inquirer=self.request.user)
        
        # Create a chat room for this inquiry
        chat_room = ChatRoom.objects.create(
            room_type='INQUIRY',
            property=inquiry.property
        )
        
        # Add members to chat room
        ChatRoomMember.objects.create(
            chat_room=chat_room,
            user=self.request.user
        )
        ChatRoomMember.objects.create(
            chat_room=chat_room,
            user=inquiry.property.owner
        )
        
        inquiry.chat_room = chat_room
        inquiry.save()
