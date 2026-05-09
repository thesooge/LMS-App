
from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/chat/', views.course_chat, name="course_chat"),
    path('course/<int:course_id>/enroll/', views.enroll, name="enroll_course"),
    path('my_courses/', views.my_courses, name="my_courses"),
    path('course/new/', views.CourseCreateView.as_view(), name="course_create"),
    path("course/<int:course_id>/lesson/new/", views.LessonCreateView.as_view(), name="lesson_create"),
    path('course/<int:course_id>/quizzes/new/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('quizzes/<int:quiz_id>/questions/new/', views.QuestionCreateView.as_view(), name='question_create'),
    path('quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<int:quiz_id>/start/', views.quiz_start, name='quiz_start'),
    path('attempts/<int:attempt_id>/questions/<int:question_id>/', views.quiz_question, name='quiz_question'),
    path('attempts/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    path('questions/<int:question_id>/choices/new/', views.answerchoice_create, name='answerchoice_create'),
]
