from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import student_required
from careers.models import get_assessment
from careers.rules import generate_suggestions
from results.models import StudentSubject, SemesterStudyTime
from .models import TeacherAccessGrant


def _is_teacher(user):
    profile = getattr(user, 'profile', None)
    return profile is not None and profile.role == 'teacher'


def _extract_token(text):
    """Accepts a full invite link, a partial path, or the bare code, and
    returns just the token (the last path segment)."""
    path = urlparse((text or '').strip()).path
    parts = [p for p in path.split('/') if p]
    return parts[-1] if parts else ''


def _claim_invite(request, token):
    """Attach the current teacher to the invite. Returns a redirect."""
    grant = TeacherAccessGrant.objects.filter(invite_token=token).select_related('student').first()
    if grant is None:
        messages.error(request, "That invite link isn't valid. Ask the student to generate a new one.")
        return redirect('my_students')

    profile = request.user.profile
    # Conditional update so two teachers can't both claim one invite.
    claimed = TeacherAccessGrant.objects.filter(pk=grant.pk, is_active=False).update(
        teacher=profile, is_active=True, accepted_at=timezone.now()
    )
    if claimed:
        messages.success(request, f"You now have access to {grant.student.full_name}'s progress.")
    elif grant.teacher_id == profile.id:
        messages.info(request, f"You already have access to {grant.student.full_name}'s progress.")
    else:
        messages.error(request, "That invite has already been used by another teacher.")
    return redirect('my_students')


@student_required
def manage_access_view(request):
    """Student side: generate invite links, see pending/active grants, revoke."""
    student = request.student

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'generate':
            TeacherAccessGrant.objects.create(student=student)
        elif action == 'revoke':
            grant_id = request.POST.get('grant_id')
            grant = get_object_or_404(TeacherAccessGrant, id=grant_id, student=student)
            grant.delete()
        return redirect('manage_teacher_access')

    grants = TeacherAccessGrant.objects.filter(student=student).select_related('teacher__user').order_by('-created_at')
    return render(request, 'teacher_access/manage_access.html', {'grants': grants})


@login_required
def accept_invite_view(request, token):
    if not _is_teacher(request.user):
        messages.error(request, "Only teacher accounts can accept a student invite link.")
        return redirect('dashboard')
    return _claim_invite(request, token)


@login_required
@require_POST
def join_invite_view(request):
    """Teacher side: paste an invite link (or code) instead of opening it."""
    if not _is_teacher(request.user):
        return redirect('dashboard')
    token = _extract_token(request.POST.get('invite'))
    if not token:
        messages.error(request, "Paste the invite link your student sent you.")
        return redirect('my_students')
    return _claim_invite(request, token)


@login_required
def my_students_view(request):
    if not _is_teacher(request.user):
        return redirect('dashboard')

    grants = TeacherAccessGrant.objects.filter(
        teacher=request.user.profile, is_active=True
    ).select_related('student', 'student__course')
    return render(request, 'teacher_access/my_students.html', {'grants': grants})


@login_required
def student_detail_view(request, grant_id):
    if not _is_teacher(request.user):
        return redirect('dashboard')

    grant = get_object_or_404(TeacherAccessGrant, id=grant_id, teacher=request.user.profile, is_active=True)
    student = grant.student

    subjects = list(
        StudentSubject.objects.filter(student=student, subject__course=student.course)
        .select_related('subject').prefetch_related('results')
    )

    assessment = get_assessment(student)
    suggestions = []
    if assessment and assessment.communication_skill is not None:
        latest_study_time = SemesterStudyTime.objects.filter(student=student).order_by('-semester').first()
        study_time = latest_study_time.study_time if latest_study_time else None
        suggestions = generate_suggestions(assessment, subjects, study_time)[:3]

    return render(request, 'teacher_access/student_detail.html', {
        'student': student,
        'subjects': subjects,
        'assessment': assessment,
        'suggestions': suggestions,
    })
