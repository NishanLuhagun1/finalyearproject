from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect

from careers.models import get_assessment
from careers.rules import generate_suggestions
from results.models import StudentSubject, SemesterStudyTime
from spp_core.utils import get_semester
from students.models import Student, Goal
from .decorators import student_required
from .forms import StudentRegistrationForm


class RememberMeLoginView(LoginView):
    """Login that honours the "Remember me" checkbox: unticked means the
    session ends when the browser closes."""
    template_name = 'registration/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)
        return response


def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # All-or-nothing: a failure while creating the Student must not
                # leave behind a user account that has no student record.
                with transaction.atomic():
                    user = form.save()
                    profile = user.profile
                    if form.cleaned_data['role'] == 'teacher':
                        profile.role = 'teacher'
                        profile.save()
                    else:
                        Student.objects.create(
                            profile=profile,
                            student_id=form.cleaned_data['student_id'],
                            full_name=form.cleaned_data['full_name'],
                            address=form.cleaned_data['address'],
                            contact=form.cleaned_data['contact'],
                            college_name=form.cleaned_data['college_name'],
                            course=form.cleaned_data['course'],
                        )
                return redirect('login')
            except IntegrityError:
                form.add_error(None, 'That username or student ID was just taken. Please try again.')
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@student_required
def dashboard_view(request):
    student = request.student

    subjects = StudentSubject.objects.filter(
        student=student, subject__course=student.course
    ).select_related('subject').prefetch_related('results')

    semesters = {}
    for ss in subjects:
        sem = ss.semester
        if sem not in semesters:
            semesters[sem] = {'semester': sem, 'subject_count': 0, 'marks_done': 0}
        semesters[sem]['subject_count'] += 1
        exam_types_entered = {r.exam_type for r in ss.results.all()}
        if 'midterm' in exam_types_entered and 'preboard' in exam_types_entered:
            semesters[sem]['marks_done'] += 1

    semester_list = sorted(semesters.values(), key=lambda s: s['semester'])
    for s in semester_list:
        s['complete'] = s['subject_count'] > 0 and s['subject_count'] == s['marks_done']

    default_semester = semester_list[-1]['semester'] if semester_list else 1
    active_semester = get_semester(request, default_semester)

    total_subjects = subjects.count()
    career_assessment = get_assessment(student)

    subject_trend = []
    subject_scores = []
    for ss in subjects:
        if ss.semester != active_semester:
            continue
        results_by_type = {r.exam_type: r.weighted_score for r in ss.results.all() if r.weighted_score is not None}
        g1 = results_by_type.get('midterm')
        g2 = results_by_type.get('preboard')

        scores = [v for v in (g1, g2) if v is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        if avg_score is not None:
            subject_scores.append({'name': ss.subject.name, 'score': avg_score})

        trend = None
        if g1 is not None and g2 is not None:
            delta = round(g2 - g1, 1)
            trend = {'delta': delta, 'direction': 'up' if delta >= 0 else 'down'}

        subject_trend.append({
            'name': ss.subject.name, 'g1': g1, 'g2': g2,
            'average': avg_score, 'trend': trend,
        })

    has_active_subjects = subjects.filter(semester=active_semester).exists()

    CHART_COLORS = ['#0F8C82', '#E8A33D', '#3B82F6', '#8B5CF6', '#EF4444', '#14B8A6', '#F59E0B', '#6366F1']
    CHART_TOP, CHART_BOTTOM = 20, 180

    all_chart_scores = [v for s in subject_trend if s['g1'] is not None and s['g2'] is not None for v in (s['g1'], s['g2'])]

    if all_chart_scores:
        raw_min, raw_max = min(all_chart_scores), max(all_chart_scores)
        padding = max(5, (raw_max - raw_min) * 0.15)
        chart_min = max(0, round(raw_min - padding))
        chart_max = min(100, round(raw_max + padding))
        if chart_max == chart_min:
            chart_min, chart_max = max(0, chart_min - 10), min(100, chart_max + 10)
    else:
        chart_min, chart_max = 0, 100

    def score_to_y(score):
        span = chart_max - chart_min
        pct = (score - chart_min) / span if span else 0.5
        return round(CHART_BOTTOM - pct * (CHART_BOTTOM - CHART_TOP), 1)

    subject_trend_chart = []
    color_index = 0
    for s in subject_trend:
        if s['g1'] is not None and s['g2'] is not None:
            subject_trend_chart.append({
                'name': s['name'], 'g1': s['g1'], 'g2': s['g2'],
                'y1': score_to_y(s['g1']), 'y2': score_to_y(s['g2']),
                'color': CHART_COLORS[color_index % len(CHART_COLORS)],
                'trend_label': f"+{s['trend']['delta']}%" if s['trend']['direction'] == 'up' else f"{s['trend']['delta']}%",
            })
            color_index += 1

    chart_gridlines = []
    if all_chart_scores:
        for i in range(5):
            val = chart_min + (chart_max - chart_min) * i / 4
            chart_gridlines.append({'y': score_to_y(val), 'label': f"{round(val)}%"})

    overall_standing = round(sum(s['score'] for s in subject_scores) / len(subject_scores), 1) if subject_scores else None

    study_time_entry = SemesterStudyTime.objects.filter(student=student, semester=active_semester).first()
    study_time = study_time_entry.study_time if study_time_entry else None

    top_suggestions = []
    if career_assessment and career_assessment.communication_skill is not None:
        active_subjects = subjects.filter(semester=active_semester)
        top_suggestions = generate_suggestions(career_assessment, active_subjects, study_time)[:3]

    student_goals = Goal.objects.filter(student=student)
    goal_count = student_goals.count()
    goals_pending = student_goals.filter(is_completed=False).count()

    context = {
        'student': student,
        'semester_list': semester_list,
        'semester_choices': range(1, 9),
        'total_subjects': total_subjects,
        'active_semester': active_semester,
        'career_assessment': career_assessment,
        'subject_scores': subject_scores,
        'subject_trend': subject_trend,
        'subject_trend_chart': subject_trend_chart,
        'chart_gridlines': chart_gridlines,
        'has_active_subjects': has_active_subjects,
        'overall_standing': overall_standing,
        'top_suggestions': top_suggestions,
        'goal_count': goal_count,
        'goals_pending': goals_pending,
    }
    return render(request, 'dashboard.html', context)


@student_required
def search_view(request):
    query = request.GET.get('q', '').strip()
    student = request.student
    subject_results = []
    goal_results = []

    if query:
        subjects = StudentSubject.objects.filter(
            student=student, subject__name__icontains=query
        ).select_related('subject')
        subject_results = [{'name': ss.subject.name, 'semester': ss.semester} for ss in subjects]

        goals = Goal.objects.filter(student=student, title__icontains=query)
        goal_results = list(goals)

    return render(request, 'search_results.html', {
        'query': query,
        'subject_results': subject_results,
        'goal_results': goal_results,
    })
