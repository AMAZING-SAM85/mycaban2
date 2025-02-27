# notifications/tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import ChatRoom, Message, ChatRoomMember, PropertyInquiry
from users.models import User
from properties.models import Property

class ChatRoomModelTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Property Owner",
            user_type="OWNER",
            phone_number="+2341234567890",
            is_active=True,
            is_verified=True,
        )
        
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="testpass123",
            full_name="Property Buyer",
            user_type="BUYER",
            phone_number="+2341234567891",
            is_active=True,
            is_verified=True,
        )
        
        self.chat_room = ChatRoom.objects.create(room_type="DIRECT")
        
        ChatRoomMember.objects.create(
            chat_room=self.chat_room,
            user=self.owner
        )
        
        ChatRoomMember.objects.create(
            chat_room=self.chat_room,
            user=self.buyer
        )
    
    def test_chat_room_creation(self):
        self.assertEqual(self.chat_room.room_type, "DIRECT")
        self.assertEqual(self.chat_room.members.count(), 2)
    
    def test_messaging(self):
        message = Message.objects.create(
            chat_room=self.chat_room,
            sender=self.buyer,
            content="Hello, I'm interested in your property"
        )
        
        self.assertEqual(message.content, "Hello, I'm interested in your property")
        self.assertEqual(message.sender, self.buyer)
        self.assertFalse(message.is_read)

class ChatAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test users
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="testpass123",
            full_name="Property Owner",
            user_type="OWNER",
            phone_number="+2341234567890",
            is_active=True,
            is_verified=True,
        )
        
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="testpass123",
            full_name="Property Buyer",
            user_type="BUYER",
            phone_number="+2341234567891",
            is_active=True,
            is_verified=True,
        )
        
        # Create a property
        self.property = Property.objects.create(
            owner=self.owner,
            title="Test Property",
            # Add other required fields
        )
        
        # Login as buyer
        self.client.force_authenticate(user=self.buyer)
    
    def test_create_inquiry(self):
        url = reverse('inquiry-list')
        data = {
            'property': self.property.id,
            'subject': 'Testing inquiry',
            'message': 'I would like to know more about this property'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PropertyInquiry.objects.count(), 1)
        self.assertEqual(ChatRoom.objects.count(), 1)
        
        # Check that a chat room was created with both users
        chat_room = ChatRoom.objects.first()
        self.assertEqual(chat_room.members.count(), 2)
    
    def test_send_message(self):
        # First create an inquiry
        inquiry_url = reverse('inquiry-list')
        inquiry_data = {
            'property': self.property.id,
            'subject': 'Testing inquiry',
            'message': 'I would like to know more about this property'
        }
        
        inquiry_response = self.client.post(inquiry_url, inquiry_data, format='json')
        
        # Now send a message to the created chat room
        chat_room = ChatRoom.objects.first()
        message_url = reverse('chatroom-send-message', args=[chat_room.id])
        
        message_data = {
            'content': 'This is a test message'
        }
        
        response = self.client.post(message_url, message_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().content, 'This is a test message')