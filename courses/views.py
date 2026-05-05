from django.shortcuts import get_object_or_404, render, redirect
from .models import Course, Enrollment

from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required


# Create your views here.

def course_list(request):
    courses = Course.objects.all().order_by('-created_at')
    return render(request, 'courses/course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course,id=course_id)
    
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
    