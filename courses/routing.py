from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/courses/(?P<course_id>\d+)/chat/$', consumers.CourseChatCounsumer.as_asgi()),
]