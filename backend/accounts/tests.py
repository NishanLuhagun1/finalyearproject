from django.contrib.auth.models import User
from django.test import TestCase

from spp_core.testing import PASSWORD, make_student, make_teacher
from students.models import Course, Student


class RegistrationTests(TestCase):
    def _payload(self, **overrides):
        data = {
            'role': 'student', 'username': 'newbie', 'password1': PASSWORD, 'password2': PASSWORD,
            'full_name': 'New Student', 'student_id': 'S900', 'course': Course.objects.get(name='BIT').id,
        }
        data.update(overrides)
        return data

    def test_student_can_register(self):
        response = self.client.post('/accounts/register/', self._payload())
        self.assertRedirects(response, '/accounts/login/')
        self.assertTrue(Student.objects.filter(student_id='S900').exists())

    def test_duplicate_student_id_is_a_form_error_and_leaves_no_orphan_user(self):
        make_student('first', 'S900')
        response = self.client.post('/accounts/register/', self._payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already registered')
        self.assertFalse(User.objects.filter(username='newbie').exists())

    def test_teacher_can_register_without_student_fields(self):
        response = self.client.post('/accounts/register/', self._payload(
            role='teacher', username='mr_t', student_id='', course=''))
        self.assertRedirects(response, '/accounts/login/')
        user = User.objects.get(username='mr_t')
        self.assertEqual(user.profile.role, 'teacher')
        self.assertFalse(Student.objects.filter(profile=user.profile).exists())

    def test_student_needs_id_and_course(self):
        response = self.client.post('/accounts/register/', self._payload(student_id='', course=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie').exists())


class LoginTests(TestCase):
    def test_remember_me_unticked_makes_session_expire_on_browser_close(self):
        make_student()
        self.client.post('/accounts/login/', {'username': 'stu', 'password': PASSWORD})
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_remember_me_ticked_keeps_session(self):
        make_student()
        self.client.post('/accounts/login/', {'username': 'stu', 'password': PASSWORD, 'remember_me': '1'})
        self.assertFalse(self.client.session.get_expire_at_browser_close())


class NonStudentAccessTests(TestCase):
    STUDENT_PAGES = [
        '/accounts/dashboard/', '/accounts/search/?q=a', '/results/analytics/', '/results/add-subject/',
        '/results/add-marks/', '/results/score-summary/', '/careers/roadmap/', '/careers/interest/',
        '/careers/soft-skills/', '/students/profile/', '/students/goals/', '/teacher-access/manage/',
    ]

    def test_teacher_is_redirected_not_crashed(self):
        make_teacher()
        self.client.login(username='teach', password=PASSWORD)
        for url in self.STUDENT_PAGES:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302, url)
            self.assertEqual(response['Location'], '/teacher-access/my-students/', url)

    def test_admin_without_student_record_is_sent_to_admin(self):
        User.objects.create_superuser('boss', 'b@example.com', PASSWORD)
        self.client.login(username='boss', password=PASSWORD)
        for url in self.STUDENT_PAGES:
            self.assertEqual(self.client.get(url).status_code, 302, url)

    def test_plain_user_without_student_gets_explanation(self):
        User.objects.create_user('ghost', password=PASSWORD)
        self.client.login(username='ghost', password=PASSWORD)
        self.assertEqual(self.client.get('/accounts/dashboard/').status_code, 403)

    def test_anonymous_is_sent_to_login(self):
        response = self.client.get('/accounts/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].startswith('/accounts/login/'))


class SemesterParameterTests(TestCase):
    def test_garbage_semester_values_do_not_crash(self):
        make_student()
        self.client.login(username='stu', password=PASSWORD)
        for url in ['/accounts/dashboard/', '/results/add-subject/', '/results/add-marks/',
                    '/results/score-summary/', '/careers/interest/', '/careers/soft-skills/']:
            for bad in ('abc', '', '99', '-3', '2.5'):
                self.assertEqual(self.client.get(f'{url}?semester={bad}').status_code, 200, (url, bad))
