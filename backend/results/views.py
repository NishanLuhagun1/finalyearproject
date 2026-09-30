import math

from django.db import transaction
from django.shortcuts import render, redirect

from accounts.decorators import student_required
from careers.models import get_assessment
from careers.rules import generate_suggestions
from spp_core.utils import get_semester
from .forms import StudentSubjectForm
from .ml.predictor import predict_grade
from .models import StudentSubject, Result, SemesterStudyTime

EXAM_TYPES = [('midterm', 'Midterm'), ('preboard', 'Preboard')]

# field -> (min, max, label). The assignment is marked out of 20 (the
# weighted-score formula scales it to a percentage).
MARK_FIELDS = {
    'assignment': (0, 20, 'Assignment score'),
    'exam': (0, 100, 'Exam score'),
    'attendance': (0, 100, 'Attendance %'),
}

ATTENDANCE_PASS = 80
EXAM_PASS = 40


def _parse_marks(post, exam_type, ss_id):
    """Returns (raw_strings, values_or_None, errors). Blank = nothing entered."""
    raw = {f: post.get(f'{f}_{exam_type}_{ss_id}', '').strip() for f in MARK_FIELDS}
    if not any(raw.values()):
        return raw, None, []

    values, errors = {}, []
    for field, (low, high, label) in MARK_FIELDS.items():
        text = raw[field]
        if text == '':
            errors.append(f"{label} is missing (fill all three fields or leave the set blank)")
            continue
        try:
            number = float(text)
        except ValueError:
            errors.append(f"{label} must be a number")
            continue
        if not math.isfinite(number) or not low <= number <= high:
            errors.append(f"{label} must be between {low} and {high}")
            continue
        values[field] = number
    return raw, (None if errors else values), errors


def _weighted_score(values):
    assignment_percent = values['assignment'] / MARK_FIELDS['assignment'][1] * 100
    return round(assignment_percent * 0.30 + values['exam'] * 0.60 + values['attendance'] * 0.10, 2)


def _fmt(number):
    return '' if number is None else f"{number:g}"


@student_required
def add_subject_view(request):
    student = request.student
    selected_semester = get_semester(request)

    if request.method == 'POST':
        form = StudentSubjectForm(request.POST, student=student, semester=selected_semester)
        if form.is_valid():
            subject_entry = form.save(commit=False)
            subject_entry.student = student
            subject_entry.save()
            return redirect(f"/results/add-subject/?semester={subject_entry.semester}")
    else:
        form = StudentSubjectForm(initial={'semester': selected_semester}, student=student, semester=selected_semester)

    added_subjects = StudentSubject.objects.filter(
        student=student, semester=selected_semester, subject__course=student.course
    ).select_related('subject').prefetch_related('results').order_by('-added_at')

    subject_status = []
    for ss in added_subjects:
        exam_types = {r.exam_type for r in ss.results.all()}
        subject_status.append({
            'subject_obj': ss,
            'has_midterm': 'midterm' in exam_types,
            'has_preboard': 'preboard' in exam_types,
        })

    return render(request, 'results/add_subject.html', {
        'form': form,
        'subject_status': subject_status,
        'selected_semester': selected_semester,
        'semester_choices': range(1, 9),
        'no_subjects_available': not form.fields['subject'].queryset.exists(),
        'student_course': student.course,
    })


@student_required
def add_marks_view(request):
    student = request.student
    selected_semester = get_semester(request)
    student_subjects = list(
        StudentSubject.objects.filter(
            student=student, semester=selected_semester, subject__course=student.course
        ).select_related('subject').prefetch_related('results')
    )
    study_time_entry = SemesterStudyTime.objects.filter(student=student, semester=selected_semester).first()
    study_time_value = study_time_entry.study_time if study_time_entry else 2
    errors = []
    entries = []

    if request.method == 'POST':
        to_save = []
        for ss in student_subjects:
            entry = {'ss': ss}
            for exam_type, exam_label in EXAM_TYPES:
                raw, values, set_errors = _parse_marks(request.POST, exam_type, ss.id)
                entry[exam_type] = raw
                errors += [f"{ss.subject.name} ({exam_label}): {e}" for e in set_errors]
                if values:
                    to_save.append((ss, exam_type, values))
            entries.append(entry)

        posted_study_time = request.POST.get('study_time')
        if posted_study_time:
            if posted_study_time in {str(v) for v, _ in SemesterStudyTime.STUDY_TIME_CHOICES}:
                study_time_value = int(posted_study_time)
            else:
                errors.append("Choose one of the listed study-time options")
                posted_study_time = None

        if not errors:
            with transaction.atomic():
                for ss, exam_type, values in to_save:
                    Result.objects.update_or_create(
                        student_subject=ss,
                        exam_type=exam_type,
                        defaults={
                            'assignment_score': values['assignment'],
                            'exam_score': values['exam'],
                            'attendance_percent': values['attendance'],
                            'is_eligible': (
                                values['attendance'] >= ATTENDANCE_PASS
                                and values['exam'] >= EXAM_PASS
                                and values['assignment'] > 0  # an assignment was actually submitted
                            ),
                            'weighted_score': _weighted_score(values),
                        }
                    )
                if posted_study_time:
                    SemesterStudyTime.objects.update_or_create(
                        student=student, semester=selected_semester,
                        defaults={'study_time': study_time_value},
                    )
            return redirect(f"/careers/interest/?semester={selected_semester}")
    else:
        for ss in student_subjects:
            existing = {r.exam_type: r for r in ss.results.all()}
            entry = {'ss': ss}
            for exam_type, _ in EXAM_TYPES:
                r = existing.get(exam_type)
                entry[exam_type] = {
                    'assignment': _fmt(r.assignment_score if r else None),
                    'exam': _fmt(r.exam_score if r else None),
                    'attendance': _fmt(r.attendance_percent if r else None),
                }
            entries.append(entry)

    return render(request, 'results/add_marks.html', {
        'entries': entries,
        'errors': errors,
        'selected_semester': selected_semester,
        'study_time_value': study_time_value,
        'study_time_choices': SemesterStudyTime.STUDY_TIME_CHOICES,
    })


@student_required
def score_summary_view(request):
    student = request.student
    selected_semester = get_semester(request)
    student_subjects = list(
        StudentSubject.objects.filter(
            student=student, semester=selected_semester, subject__course=student.course
        ).select_related('subject').prefetch_related('results')
    )
    assessment = get_assessment(student)
    study_time_entry = SemesterStudyTime.objects.filter(student=student, semester=selected_semester).first()
    study_time = study_time_entry.study_time if study_time_entry else None

    suggestions = []
    if assessment:
        suggestions = generate_suggestions(assessment, student_subjects, study_time)[:3]

    for ss in student_subjects:
        results_by_type = {r.exam_type: r for r in ss.results.all()}
        midterm = results_by_type.get('midterm')
        preboard = results_by_type.get('preboard')
        if midterm and preboard and midterm.weighted_score is not None and preboard.weighted_score is not None:
            predicted = predict_grade(study_time, midterm.weighted_score, preboard.weighted_score)
            for r in (midterm, preboard):
                if r.predicted_score != predicted:
                    r.predicted_score = predicted
                    r.save(update_fields=['predicted_score'])

    return render(request, 'results/score_summary.html', {
        'student_subjects': student_subjects,
        'assessment': assessment,
        'suggestions': suggestions,
        'selected_semester': selected_semester,
    })


@student_required
def analytics_view(request):
    student = request.student
    all_subjects = StudentSubject.objects.filter(
        student=student, subject__course=student.course
    ).select_related('subject').prefetch_related('results')

    semester_scores = {}
    subject_rows = []
    eligible_count = 0
    total_results = 0

    for ss in all_subjects:
        scores = []
        for r in ss.results.all():
            if r.weighted_score is not None:
                scores.append(r.weighted_score)
                total_results += 1
                if r.is_eligible:
                    eligible_count += 1
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        semester_scores.setdefault(ss.semester, []).append(avg)
        subject_rows.append({'name': ss.subject.name, 'semester': ss.semester, 'score': round(avg, 1)})

    semester_trend = [
        {'semester': sem, 'average': round(sum(vals) / len(vals), 1)}
        for sem, vals in sorted(semester_scores.items())
    ]

    # Auto-scaled line chart coordinates -- same approach as the dashboard chart,
    # so both pages share one visual language instead of two different chart styles.
    CHART_TOP, CHART_BOTTOM, CHART_LEFT, CHART_RIGHT = 20, 160, 60, 420
    chart_points = []
    chart_gridlines = []

    if semester_trend:
        values = [s['average'] for s in semester_trend]
        raw_min, raw_max = min(values), max(values)
        padding = max(5, (raw_max - raw_min) * 0.2)
        chart_min = max(0, round(raw_min - padding))
        chart_max = min(100, round(raw_max + padding))
        if chart_max == chart_min:
            chart_min, chart_max = max(0, chart_min - 10), min(100, chart_max + 10)

        def score_to_y(score):
            span = chart_max - chart_min
            pct = (score - chart_min) / span if span else 0.5
            return round(CHART_BOTTOM - pct * (CHART_BOTTOM - CHART_TOP), 1)

        n = len(semester_trend)
        for i, s in enumerate(semester_trend):
            x = CHART_LEFT if n == 1 else CHART_LEFT + i * (CHART_RIGHT - CHART_LEFT) / (n - 1)
            chart_points.append({'x': round(x, 1), 'y': score_to_y(s['average']), 'label': f"Sem {s['semester']}", 'value': s['average']})

        for i in range(5):
            val = chart_min + (chart_max - chart_min) * i / 4
            chart_gridlines.append({'y': score_to_y(val), 'label': f"{round(val)}%"})

    chart_line_points = " ".join(f"{p['x']},{p['y']}" for p in chart_points)

    subject_rows.sort(key=lambda r: r['score'], reverse=True)

    overall_average = round(sum(r['score'] for r in subject_rows) / len(subject_rows), 1) if subject_rows else None
    eligibility_rate = round((eligible_count / total_results) * 100) if total_results else None

    return render(request, 'results/analytics.html', {
        'semester_trend': semester_trend,
        'chart_points': chart_points,
        'chart_line_points': chart_line_points,
        'chart_gridlines': chart_gridlines,
        'subject_rows': subject_rows,
        'overall_average': overall_average,
        'eligibility_rate': eligibility_rate,
        'total_subjects': len(subject_rows),
        'semesters_tracked': len(semester_trend),
        'has_data': bool(subject_rows),
    })
