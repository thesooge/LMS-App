from django.contrib import admin
from .models import Course, Lesson, Message, Question, Quiz, QuizAttempt
# Register your models here.
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Message)
admin.site.register(QuizAttempt)
admin.site.register(Quiz)
admin.site.register(Question)
