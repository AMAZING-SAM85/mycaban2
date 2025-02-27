import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message, ChatRoomMember
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger('django')

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Log connection attempt
        logger.debug(f"WebSocket connect attempt: room_id={self.room_id}, user={self.scope['user']}")
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept the connection
        await self.accept()
        
        # Update last_read for this user in this room if authenticated
        if not isinstance(self.scope['user'], AnonymousUser):
            await self.update_last_read()
            # Send a connection confirmation message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to chat room',
                'user_id': self.scope['user'].id
            }))
        else:
            # Inform client about authentication requirement
            await self.send(text_data=json.dumps({
                'error': 'Authentication required',
                'detail': 'Valid JWT token required in query parameter "token"'
            }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.debug(f"WebSocket disconnected: room_id={self.room_id}, code={close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message', '')
            
            logger.debug(f"Message receive: {text_data}")
            
            if isinstance(self.scope['user'], AnonymousUser):
                await self.send(text_data=json.dumps({
                    'error': 'Authentication required',
                    'detail': 'You must be authenticated to send messages'
                }))
                return
            
            # Save message to database
            message = await self.save_message(message_content)
            if not message:
                await self.send(text_data=json.dumps({
                    'error': 'Failed to save message',
                    'detail': 'You may not be a member of this chat room'
                }))
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
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Server error',
                'detail': str(e)
            }))

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
                logger.warning(f"User {user.id} attempted to send message in room {self.room_id} but is not a member")
                return None
                
            message = Message.objects.create(
                chat_room=chat_room,
                sender=user,
                content=content
            )
            
            logger.debug(f"Message saved: id={message.id}, sender={user.id}, room={self.room_id}")
            
            return {
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.full_name,
                'created_at': message.created_at,
            }
        except ChatRoom.DoesNotExist:
            logger.error(f"Chat room {self.room_id} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
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
                
            # Mark messages as read - note: changed 'sender__id__ne' to exclude messages from current user
            Message.objects.filter(
                chat_room=chat_room,
                created_at__lte=timezone.now(),
                sender__id__isnull=False
            ).exclude(sender=user).update(is_read=True)
                
            logger.debug(f"Last read updated for user {user.id} in room {self.room_id}")
                
        except ChatRoom.DoesNotExist:
            logger.error(f"Chat room {self.room_id} does not exist")
            pass
        except Exception as e:
            logger.error(f"Error updating last read: {str(e)}")
            pass