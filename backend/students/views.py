from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.decorators import student_required
from .forms import GoalForm, StudentCourseForm
from .models import Goal


@student_required
def profile_view(request):
    student = request.student

    if request.method == 'POST':
        course_form = StudentCourseForm(request.POST, instance=student)
        if course_form.is_valid():
            course_form.save()
            return redirect('student_profile')
    else:
        course_form = StudentCourseForm(instance=student)

    return render(request, 'students/profile.html', {
        'student': student,
        'course_form': course_form,
    })


@student_required
def goal_list_view(request):
    student = request.student

    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.student = student
            goal.save()
            return redirect('goal_list')
    else:
        form = GoalForm()

    goals = Goal.objects.filter(student=student).order_by('is_completed', 'target_date')

    return render(request, 'students/goal_list.html', {
        'form': form,
        'goals': goals,
    })


# State changes are POST-only (the templates submit a small CSRF-protected
# form) so a link on another site can't toggle or delete a student's goals.
@student_required
@require_POST
def toggle_goal_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, student=request.student)
    goal.is_completed = not goal.is_completed
    goal.save()
    return redirect('goal_list')


@student_required
@require_POST
def delete_goal_view(request, goal_id):
    goal = get_object_or_404(Goal, id=goal_id, student=request.student)
    goal.delete()
    return redirect('goal_list')
