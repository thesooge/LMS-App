from django.shortcuts import get_object_or_404, render, redirect
from .models import Course, Enrollment, Lesson, Quiz, Question, QuizAttempt, Response, AnswerChoice

from django.http import HttpResponseForbidden

from django.db.models import Count
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_http_methods


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
    
@login_required
def course_chat(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', course_id=course.pk)
    
    messages = course.messages.select_related('user').all()

    return render(
        request,
        'courses/course_chat.html',
        {
            'course':course,
            'messages': messages,
        },
    )


class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    fields = ["title", "description"]
    template_name = "courses/quiz_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs["course_id"])
        if request.user != self.course.creator:
            return HttpResponseForbidden("You are not allowed to add quizzes to this course.")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)
    
    def get_success_url(self):
        return self.course.get_absolute_url()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = self.course
        return context

class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    fields = ['text', 'order']
    template_name = "courses/question_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, pk=self.kwargs["quiz_id"])
        if request.user != self.quiz.course.creator:
            return HttpResponseForbidden("You are not allowed to add quizzes to this course.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.quiz = self.quiz
        return super().form_valid(form)
    
    def get_success_url(self):
        # After creating a question, go to add choices
        return reverse_lazy('answerchoice_create', kwargs={'question_id': self.object.id})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.quiz
        return context
    
@login_required
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    #enrollment check
    if not Enrollment.objects.filter(user=request.user, course=quiz.course).exists():
        return redirect('course_detail', course_id=quiz.course.pk)
    
    questions = Question.objects.all()

    return render(request, 'courses/quiz_detail.html', context={
        'quiz': quiz,
        'questions': questions,
    })

@login_required    
def quiz_start(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)

    #enrollment check
    if not Enrollment.objects.filter(user=request.user, course=quiz.course).exists():
        return redirect('course_detail', course_id=quiz.course.pk)
    
    attempt = QuizAttempt.objects.create(
        user= request.user,
        quiz = quiz,
        started_at= timezone.now(),
    )

    first_question = quiz.questions.order_by('order').first()
    if not first_question:
        # No questions, mark attempt completed with score 0
        attempt.completed = True
        attempt.score = 0
        attempt.completed_at = timezone.now()
        attempt.save()
        return redirect('quiz_detail', quiz_id=quiz.pk)
    
    return redirect('quiz_question', attempt_id=attempt.id, question_id=first_question.id)

@login_required
def quiz_question(request, attempt_id, question_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    question = get_object_or_404(Question, pk=question_id, quiz= attempt.quiz)
    choices = question.answerchoices.all()

    if request.method == "POST":
        choice_id = request.POST.get('choice')
        selected_choice = None
        if choice_id:
            selected_choice = get_object_or_404(AnswerChoice, pk=choice_id, question=question)

        response, created = Response.objects.update_or_create(
            attempt = attempt,
            question = question,
            defaults={'selected_choice' : selected_choice},
        )    

        questions = list(attempt.quiz.questions.order_by('order'))
        current_index = questions.index(question)
        if current_index + 1 < len(questions):
            next_question = questions[current_index+1]
            return redirect('quiz_question', attempt_id=attempt.id, question_id=next_question.id)
        else:
            total = len(questions)
            correct = Response.objects.filter(
                attempt=attempt,
                selected_choice__is_correct=True
            ).count()
            attempt.score = (correct / total) * 100 if total > 0 else 0
            attempt.completed = True
            attempt.completed_at = timezone.now()
            attempt.save()
            return redirect('quiz_result', attempt_id=attempt.id)

    return render(request, 'courses/quiz_question.html', {
        'attempt': attempt,
        'question': question,
        'choices': choices,
    })


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    responses = attempt.responses.select_related('question', 'selected_choice')
    return render(request, 'courses/quiz_result.html', {
        'attempt': attempt,
        'responses': responses,
    })    


@login_required
@require_http_methods(["GET", "POST"])
def answerchoice_create(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    # Only the creator of the course can add choices
    if question.quiz.course.creator != request.user:
        return HttpResponseForbidden("You are not allowed to add choices to this question.")

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        is_correct = bool(request.POST.get('is_correct'))

        if text:
            AnswerChoice.objects.create(
                question=question,
                text=text,
                is_correct=is_correct,
            )
            # After saving, stay on the same page so they can add more options
            return redirect('answerchoice_create', question_id=question.id)

    choices = question.answerchoices.all()
    return render(request, 'courses/answerchoice_form.html', {
        'question': question,
        'choices': choices,
    })