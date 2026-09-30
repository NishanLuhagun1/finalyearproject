from django.test import TestCase

from spp_core.testing import PASSWORD, make_student
from .models import Result, SemesterStudyTime, StudentSubject, Subject


class ResultsTestBase(TestCase):
    def setUp(self):
        self.user, self.student = make_student()
        self.client.login(username='stu', password=PASSWORD)
        self.subject = Subject.objects.filter(course=self.student.course).first()
        self.ss = StudentSubject.objects.create(student=self.student, subject=self.subject, semester=1)

    def marks(self, **overrides):
        data = {'semester': 1, 'study_time': 3}
        for exam_type in ('midterm', 'preboard'):
            data[f'assignment_{exam_type}_{self.ss.id}'] = '15'
            data[f'exam_{exam_type}_{self.ss.id}'] = '70'
            data[f'attendance_{exam_type}_{self.ss.id}'] = '90'
        data.update(overrides)
        return data


class AddSubjectTests(ResultsTestBase):
    def test_adding_same_subject_twice_is_a_form_error(self):
        response = self.client.post('/results/add-subject/?semester=1', {'subject': self.subject.id, 'semester': 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already added')
        self.assertEqual(StudentSubject.objects.filter(student=self.student).count(), 1)

    def test_same_subject_in_another_semester_is_allowed(self):
        response = self.client.post('/results/add-subject/?semester=2', {'subject': self.subject.id, 'semester': 2})
        self.assertEqual(response.status_code, 302)


class AddMarksTests(ResultsTestBase):
    def test_valid_marks_are_saved_and_scored(self):
        response = self.client.post('/results/add-marks/', self.marks())
        self.assertEqual(response.status_code, 302)
        result = Result.objects.get(student_subject=self.ss, exam_type='midterm')
        # 15/20 -> 75% * 0.3 + 70 * 0.6 + 90 * 0.1
        self.assertEqual(result.weighted_score, 73.5)
        self.assertTrue(result.is_eligible)
        self.assertEqual(SemesterStudyTime.objects.get(student=self.student, semester=1).study_time, 3)

    def test_out_of_range_and_non_numeric_marks_are_rejected(self):
        key = lambda f: f'{f}_midterm_{self.ss.id}'
        for bad in (
            {key('assignment'): '500'}, {key('exam'): '900'}, {key('attendance'): '150'},
            {key('exam'): '-1'}, {key('exam'): 'abc'}, {key('exam'): 'nan'}, {key('exam'): 'inf'},
            {key('exam'): ''},  # partially filled set
        ):
            response = self.client.post('/results/add-marks/', self.marks(**bad))
            self.assertEqual(response.status_code, 200, bad)
            self.assertContains(response, 'Please fix these', msg_prefix=str(bad))
        self.assertEqual(Result.objects.count(), 0)

    def test_nothing_is_saved_if_any_set_is_invalid(self):
        response = self.client.post('/results/add-marks/', self.marks(**{f'exam_preboard_{self.ss.id}': '999'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Result.objects.count(), 0)

    def test_zero_marks_are_stored_and_not_eligible(self):
        self.client.post('/results/add-marks/', self.marks(**{
            f'assignment_midterm_{self.ss.id}': '0', f'exam_midterm_{self.ss.id}': '0',
            f'attendance_midterm_{self.ss.id}': '0'}))
        result = Result.objects.get(student_subject=self.ss, exam_type='midterm')
        self.assertEqual(result.weighted_score, 0)
        self.assertFalse(result.is_eligible)

    def test_submitting_no_assignment_makes_result_ineligible(self):
        self.client.post('/results/add-marks/', self.marks(**{f'assignment_midterm_{self.ss.id}': '0'}))
        self.assertFalse(Result.objects.get(student_subject=self.ss, exam_type='midterm').is_eligible)

    def test_viewing_the_page_does_not_invent_a_study_time(self):
        self.client.get('/results/add-marks/?semester=1')
        self.assertFalse(SemesterStudyTime.objects.exists())

    def test_saved_marks_are_prefilled_including_zero(self):
        self.client.post('/results/add-marks/', self.marks(**{f'exam_midterm_{self.ss.id}': '0'}))
        response = self.client.get('/results/add-marks/?semester=1')
        self.assertContains(response, f'name="exam_midterm_{self.ss.id}" value="0"')

    def test_invalid_study_time_is_rejected(self):
        response = self.client.post('/results/add-marks/', self.marks(study_time='9'))
        self.assertEqual(response.status_code, 200)


class SummaryTests(ResultsTestBase):
    def test_summary_and_analytics_render_with_predictions(self):
        self.client.post('/results/add-marks/', self.marks())
        summary = self.client.get('/results/score-summary/?semester=1')
        self.assertEqual(summary.status_code, 200)
        self.assertIsNotNone(Result.objects.get(student_subject=self.ss, exam_type='midterm').predicted_score)
        self.assertEqual(self.client.get('/results/analytics/').status_code, 200)
