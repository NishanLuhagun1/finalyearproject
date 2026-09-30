from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def student_required(view):
    """Login required, and the user must actually have a Student record.

    Teachers are sent to their own page, staff/admin accounts to the admin
    site, and anyone else (a bare user with no student record) sees an
    explanation, instead of the view crashing on `profile.student`.
    The student is exposed as `request.student`.
    """
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        student = getattr(profile, 'student', None) if profile else None
        if student is None:
            if profile is not None and profile.role == 'teacher':
                return redirect('my_students')
            if request.user.is_staff:
                return redirect('admin:index')
            return render(request, 'students/no_student_profile.html', status=403)
        request.student = student
        return view(request, *args, **kwargs)
    return wrapper
