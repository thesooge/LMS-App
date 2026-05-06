from django.shortcuts import get_object_or_404, render, redirect
from .models import Course, Enrollment, Lesson

from django.http import HttpResponseForbidden

from django.db.models import Count
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


# Create your views here.

def course_list(request):
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course.objects.annotate(enrollment_count=Count("enrollment")), id= course_id)
    
    is_enrolled = False
    
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user = request.user, course = course).exists()

    return render(request, 'courses/course_detail.html', {'course': course, 'is_enrolled': is_enrolled})


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    Enrollment.objects.get_or_create(user= request.user, course= course)

    return redirect('course_detail', course_id=course.pk)

@login_required
def my_courses(request):
    enrollments = Enrollment.objects.filter(user= request.user).select_related('course')
    courses = []
    for enrollment in enrollments:
        courses.append(enrollment.course)

    return render(request, 'courses/my_courses.html', {"courses": courses})   


class CourseCreateView(CreateView):
    template_name = "courses/course_form.html"
    model = Course
    success_url = reverse_lazy("course_list")
    fields = ["title", "description"]

    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)
    

class LessonCreateView(LoginRequiredMixin, CreateView):
    model = Lesson
    fields = ["title", "description", "video_url", "order"]
    template_name = "courses/lesson_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, id=self.kwargs["course_id"])
        if self.course.creator != request.user:
            return HttpResponseForbidden("You are not allowed to add lessons to this course.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self):
        return self.course.get_absolute_url() if hasattr(self.course, 'get_absolute_url') else reverse_lazy('course_detail', kwargs={'pk': self.course.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course_id"] = self.course.id
        context["course"] = self.course
        return context
    
