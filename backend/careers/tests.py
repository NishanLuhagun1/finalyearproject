from django.test import TestCase

from results.models import Result, StudentSubject, Subject
from spp_core.testing import PASSWORD, make_student
from .models import CareerAssessment, CareerProfile, get_assessment
from .rules import generate_suggestions

SKILLS = ['communication_skill', 'teamwork_skill', 'problem_solving_skill', 'leadership_skill',
          'adaptability_skill', 'time_management_skill', 'critical_thinking_skill', 'creativity_skill',
          'programming_skill', 'database_skill', 'web_dev_skill', 'networking_skill']


def rated_assessment(student, rating=3, **extra):
    fields = {name: rating for name in SKILLS}
    fields.update(extra)
    return CareerAssessment.objects.create(student=student, interest_area='software_engineering', **fields)


def add_marks(student, subject_name, score, semester=1):
    subject = Subject.objects.get(course=student.course, name=subject_name)
    ss = StudentSubject.objects.create(student=student, subject=subject, semester=semester)
    for exam_type in ('midterm', 'preboard'):
        Result.objects.create(student_subject=ss, exam_type=exam_type, assignment_score=10, exam_score=score,
                              attendance_percent=90, weighted_score=score, is_eligible=True)
    return ss


class AssessmentHelperTests(TestCase):
    def setUp(self):
        self.user, self.student = make_student()
        self.client.login(username='stu', password=PASSWORD)

    def test_duplicate_assessments_do_not_crash_the_wizard(self):
        CareerAssessment.objects.create(student=self.student)
        CareerAssessment.objects.create(student=self.student)
        for url in ('/careers/interest/', '/careers/soft-skills/', '/careers/roadmap/'):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(get_assessment(self.student).pk, CareerAssessment.objects.order_by('pk').first().pk)

    def test_get_assessment_creates_only_when_asked(self):
        self.assertIsNone(get_assessment(self.student))
        self.assertIsNotNone(get_assessment(self.student, create=True))
        self.assertEqual(CareerAssessment.objects.count(), 1)


class SuggestionTests(TestCase):
    def setUp(self):
        self.user, self.student = make_student()

    def test_rows_are_updated_in_place_not_recreated(self):
        assessment = rated_assessment(self.student)
        first = {s.career_id: s.pk for s in generate_suggestions(assessment, [])}
        second = {s.career_id: s.pk for s in generate_suggestions(assessment, [])}
        self.assertEqual(first, second)
        self.assertEqual(len(first), CareerProfile.objects.count())

    def test_every_matching_subject_counts_not_just_the_first(self):
        # Two BIT subjects contain "Web Development"; only the second has marks.
        subject_a = Subject.objects.get(course=self.student.course, name='Web Development')
        StudentSubject.objects.create(student=self.student, subject=subject_a, semester=1)
        add_marks(self.student, 'Web Development II', 80, semester=2)
        assessment = rated_assessment(self.student)
        subjects = list(StudentSubject.objects.filter(student=self.student).prefetch_related('results'))
        se = next(s for s in generate_suggestions(assessment, subjects) if s.career.name == 'Software Engineer')
        web = next(f for f in se.roadmap['focus_subjects'] if f['name'].startswith('Web Development'))
        self.assertEqual(web['current'], 80)

    def test_tip_is_short_and_specific_to_the_weakest_subject(self):
        add_marks(self.student, 'Data Structures', 40, semester=3)
        assessment = rated_assessment(self.student)
        subjects = list(StudentSubject.objects.filter(student=self.student).prefetch_related('results'))
        se = next(s for s in generate_suggestions(assessment, subjects, study_time=1)
                  if s.career.name == 'Software Engineer')
        self.assertIn('Data Structures', se.tip)
        self.assertIn('h/week', se.tip)
        self.assertLess(len(se.tip), 140)


class RoadmapTests(TestCase):
    def setUp(self):
        self.user, self.student = make_student()
        self.client.login(username='stu', password=PASSWORD)

    def test_roadmap_lists_focus_subjects_hours_and_study_time(self):
        add_marks(self.student, 'Data Structures', 40, semester=3)
        add_marks(self.student, 'Database Systems', 90, semester=3)
        rated_assessment(self.student, rating=2)
        from results.models import SemesterStudyTime
        SemesterStudyTime.objects.create(student=self.student, semester=3, study_time=1)

        response = self.client.get('/careers/roadmap/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subjects to focus on')
        self.assertContains(response, 'Data Structures')
        self.assertContains(response, 'h/week')
        self.assertContains(response, 'Less than 2 hours/week')
        self.assertContains(response, 'Your plan')

    def test_roadmap_asks_for_assessment_first(self):
        response = self.client.get('/careers/roadmap/')
        self.assertContains(response, 'Set up career profile')

    def test_roadmap_data_shape(self):
        add_marks(self.student, 'Data Structures', 40, semester=3)
        assessment = rated_assessment(self.student, rating=5, programming_languages='Python,Java,JavaScript')
        subjects = list(StudentSubject.objects.filter(student=self.student).prefetch_related('results'))
        se = next(s for s in generate_suggestions(assessment, subjects, 4) if s.career.name == 'Software Engineer')
        focus = se.roadmap['focus_subjects']
        self.assertEqual(focus[0]['status'], 'needs_work')          # most urgent first
        self.assertEqual(focus[0]['hours'], 6)                       # 25+ points below target
        self.assertEqual(se.roadmap['languages_missing'], [])
        self.assertEqual(se.roadmap['skills'], [])
        self.assertEqual(se.roadmap['study']['status'], 'ok')
