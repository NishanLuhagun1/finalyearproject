from datetime import date, timedelta


def notifications(request):
    if not request.user.is_authenticated:
        return {'notifications': [], 'notification_count': 0}

    try:
        student = request.user.profile.student
    except Exception:
        return {'notifications': [], 'notification_count': 0}

    from results.models import StudentSubject
    from students.models import Goal
    from careers.models import get_assessment

    items = []

    if student.course is None:
        items.append({'text': "Set your course on your Profile page to see your subjects.", 'url': '/students/profile/'})
    else:
        subjects = StudentSubject.objects.filter(
            student=student, subject__course=student.course
        ).select_related('subject').prefetch_related('results')

        missing_by_semester = {}
        for ss in subjects:
            exam_types = {r.exam_type for r in ss.results.all()}
            if not ('midterm' in exam_types and 'preboard' in exam_types):
                missing_by_semester[ss.semester] = missing_by_semester.get(ss.semester, 0) + 1
        for sem, count in sorted(missing_by_semester.items()):
            items.append({
                'text': f"{count} subject{'s' if count != 1 else ''} missing marks in Semester {sem}.",
                'url': f'/results/add-marks/?semester={sem}',
            })

        assessment = get_assessment(student)
        if not assessment or not assessment.interest_area or assessment.communication_skill is None:
            items.append({'text': "Complete your career interest and skills to see suggestions.", 'url': '/careers/interest/?semester=1'})

    today = date.today()
    soon = today + timedelta(days=7)
    upcoming_goals = Goal.objects.filter(
        student=student, is_completed=False, target_date__isnull=False,
        target_date__gte=today, target_date__lte=soon
    )
    for g in upcoming_goals:
        days_left = (g.target_date - today).days
        items.append({
            'text': f"Goal \"{g.title}\" is due in {days_left} day{'s' if days_left != 1 else ''}.",
            'url': '/students/goals/',
        })

    return {'notifications': items, 'notification_count': len(items)}   