from django.shortcuts import render, redirect

from accounts.decorators import student_required
from results.models import StudentSubject, SemesterStudyTime
from spp_core.utils import get_semester
from .forms import InterestAreaForm, SoftSkillsForm
from .models import get_assessment
from .rules import generate_suggestions


@student_required
def add_interest_view(request):
    student = request.student
    assessment = get_assessment(student, create=True)
    selected_semester = get_semester(request)

    if request.method == 'POST':
        form = InterestAreaForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            return redirect(f"/careers/soft-skills/?semester={selected_semester}")
    else:
        form = InterestAreaForm(instance=assessment)

    return render(request, 'careers/add_interest.html', {
        'form': form,
        'selected_semester': selected_semester,
    })


@student_required
def add_soft_skills_view(request):
    student = request.student
    assessment = get_assessment(student, create=True)
    selected_semester = get_semester(request)

    if request.method == 'POST':
        form = SoftSkillsForm(request.POST, instance=assessment)
        if form.is_valid():
            form.save()
            return redirect(f"/results/score-summary/?semester={selected_semester}")
    else:
        form = SoftSkillsForm(instance=assessment)

    return render(request, 'careers/add_soft_skills.html', {
        'form': form,
        'selected_semester': selected_semester,
    })


@student_required
def roadmap_view(request):
    student = request.student
    assessment = get_assessment(student)
    student_subjects = list(
        StudentSubject.objects.filter(student=student, subject__course=student.course)
        .select_related('subject').prefetch_related('results')
    )
    latest_study_time = SemesterStudyTime.objects.filter(student=student).order_by('-semester').first()
    study_time = latest_study_time.study_time if latest_study_time else None

    suggestions = []
    if assessment and assessment.communication_skill is not None:
        suggestions = generate_suggestions(assessment, student_subjects, study_time)

    return render(request, 'careers/roadmap.html', {
        'assessment': assessment,
        'suggestions': suggestions,
        'has_subjects': bool(student_subjects),
    })
