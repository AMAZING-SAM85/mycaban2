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
from drf_spectacular.utils import extend_schema, OpenApiParameter

class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat rooms.
    """
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get chat rooms for the currently authenticated user.
        """
        return ChatRoom.objects.filter(
            members__user=self.request.user
        ).distinct()

    @extend_schema(
        summary="Retrieve messages in a chat room",
        description="Retrieves all messages for a given chat room and marks unread messages as read.",
    )
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Retrieve messages for a chat room.
        """
        chat_room = self.get_object()
        messages = chat_room.messages.all()
        serializer = MessageSerializer(messages, many=True)
        
        # Mark messages as read
        messages.filter(
            ~Q(sender=request.user),
            is_read=False
        ).update(is_read=True)
        
        return Response(serializer.data)

    @extend_schema(
        summary="Send a message to a chat room",
        description="Sends a new message to the specified chat room.",
        request=MessageSerializer  # Add request schema for clarity
    )
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a message to a chat room.
        """
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

    @extend_schema(summary="List chat rooms")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create chat room")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve chat room")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update chat room")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update chat room")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete chat room")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)



class PropertyInquiryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing property inquiries.
    """
    serializer_class = PropertyInquirySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Get property inquiries for the currently authenticated user.
        Owners and agents see inquiries for their properties.
        Other users see their own inquiries.
        """
        user = self.request.user
        if user.user_type in ['OWNER', 'AGENT']:
            return PropertyInquiry.objects.filter(
                property__owner=user
            )
        return PropertyInquiry.objects.filter(
            inquirer=user
        )
    
    @extend_schema(
        summary="Create a property inquiry",
        description="Creates a new property inquiry and a corresponding chat room.",
        request=PropertyInquirySerializer # Add request schema
    )
    def perform_create(self, serializer):
        """
        Create a property inquiry and associated chat room.
        """
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

    @extend_schema(summary="List property inquiries")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(summary="Create property inquiry") # Already documented in perform_create, but good to have here too
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve property inquiry")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Update property inquiry")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partial update property inquiry")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(summary="Delete property inquiry")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)