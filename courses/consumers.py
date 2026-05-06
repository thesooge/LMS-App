import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

from .models import Course, Message

User = get_user_model()

class CourseChatCounsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("CONNECT called, path:", self.scope.get('path'), "user:", self.scope.get('user'))
        self.course_id = self.scope['url_route']['kwargs']['course_id']
        self.room_group_name = f"course_chat_{self.course_id}"

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close(code="4001")
            return
        
        is_enrolled = await self.user_is_enrolled(user.id, self.course_id)
        if not is_enrolled:
            await self.close(code="4003")
            return
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()   

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )     

    async def receive(self, text_data = None, bytes_data = None):
        data = json.loads(text_data)
        message = data.get('message','').strip()
        user = self.scope['user'] 

        if not message:
            return

        saved_message = await self.save_message(
            course_id=self.course_id,
            user_id=user.id,
            content=message,
        )   

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': saved_message.id,
                'user_id': user.id,
                'username': user.username,
                'content': saved_message.content,
                'created_at': saved_message.created_at.isoformat(),
            }
        )
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'content': event['content'],
            'created_at': event['created_at'],
        }))

    @database_sync_to_async
    def save_message(self, course_id, user_id, content):
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
        return Message.objects.create(course=course, user=user, content=content)
        
    @database_sync_to_async
    def user_is_enrolled(self, user_id, course_id):
        from .models import Enrollment
        return Enrollment.objects.filter(user_id=user_id, course_id=course_id).exists()

            
