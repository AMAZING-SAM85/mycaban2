# notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message, ChatRoomMember
from users.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update last_read for this user in this room
        if self.scope['user'].is_authenticated:
            await self.update_last_read()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json.get('message', '')
        
        if not self.scope['user'].is_authenticated:
            await self.send(text_data=json.dumps({
                'error': 'Authentication required'
            }))
            return
        
        # Save message to database
        message = await self.save_message(message_content)
        if not message:
            return
            
        # Broadcast message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': message['id'],
                    'content': message['content'],
                    'sender': {
                        'id': message['sender_id'],
                        'full_name': message['sender_name'],
                    },
                    'created_at': message['created_at'].isoformat(),
                    'is_read': False
                }
            }
        )

    async def chat_message(self, event):
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

    @database_sync_to_async
    def save_message(self, content):
        try:
            user = self.scope['user']
            chat_room = ChatRoom.objects.get(id=self.room_id)
            
            # Check if user is a member of this chat room
            is_member = ChatRoomMember.objects.filter(
                chat_room=chat_room,
                user=user
            ).exists()
            
            if not is_member:
                return None
                
            message = Message.objects.create(
                chat_room=chat_room,
                sender=user,
                content=content
            )
            
            return {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.full_name,
                'created_at': message.created_at,
            }
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def update_last_read(self):
        user = self.scope['user']
        try:
            chat_room = ChatRoom.objects.get(id=self.room_id)
            member, created = ChatRoomMember.objects.get_or_create(
                chat_room=chat_room,
                user=user,
                defaults={'last_read': timezone.now()}
            )
            
            if not created:
                member.last_read = timezone.now()
                member.save()
                
            # Mark messages as read
            Message.objects.filter(
                chat_room=chat_room,
                created_at__lte=timezone.now(),
                sender__id__ne=user.id,
                is_read=False
            ).update(is_read=True)
                
        except ChatRoom.DoesNotExist:
            pass