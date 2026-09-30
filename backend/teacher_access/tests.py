from django.test import TestCase

from spp_core.testing import PASSWORD, make_student, make_teacher
from .models import TeacherAccessGrant


class InviteFlowTests(TestCase):
    def setUp(self):
        self.user, self.student = make_student()
        self.grant = TeacherAccessGrant.objects.create(student=self.student)
        self.teacher = make_teacher('teach')
        self.client.login(username='teach', password=PASSWORD)

    def claimed(self):
        self.grant.refresh_from_db()
        return self.grant.is_active and self.grant.teacher == self.teacher.profile

    def test_teacher_can_paste_the_full_link(self):
        link = f'http://testserver/teacher-access/accept/{self.grant.invite_token}/'
        response = self.client.post('/teacher-access/join/', {'invite': f'  {link}  '}, follow=True)
        self.assertTrue(self.claimed())
        self.assertContains(response, 'You now have access')

    def test_teacher_can_paste_only_the_code(self):
        self.client.post('/teacher-access/join/', {'invite': self.grant.invite_token})
        self.assertTrue(self.claimed())

    def test_invalid_code_shows_a_message_not_a_404(self):
        response = self.client.post('/teacher-access/join/', {'invite': 'http://x/teacher-access/accept/nope/'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "isn&#x27;t valid")

    def test_empty_input_is_handled(self):
        response = self.client.post('/teacher-access/join/', {'invite': '   '}, follow=True)
        self.assertContains(response, 'Paste the invite link')

    def test_opening_the_link_directly_still_works(self):
        response = self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/', follow=True)
        self.assertTrue(self.claimed())
        self.assertContains(response, 'You now have access')

    def test_my_students_page_has_the_paste_form(self):
        response = self.client.get('/teacher-access/my-students/')
        self.assertContains(response, 'name="invite"')

    def test_second_teacher_cannot_take_over_a_used_invite(self):
        self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/')
        make_teacher('teach2')
        self.client.login(username='teach2', password=PASSWORD)
        response = self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/', follow=True)
        self.assertContains(response, 'already been used')
        self.assertTrue(self.claimed())

    def test_same_teacher_reopening_is_told_they_already_have_access(self):
        self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/')
        response = self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/', follow=True)
        self.assertContains(response, 'already have access')

    def test_student_cannot_accept_or_join(self):
        self.client.login(username='stu', password=PASSWORD)
        self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/')
        self.client.post('/teacher-access/join/', {'invite': self.grant.invite_token})
        self.grant.refresh_from_db()
        self.assertFalse(self.grant.is_active)

    def test_teacher_only_sees_their_own_students(self):
        self.client.get(f'/teacher-access/accept/{self.grant.invite_token}/')
        self.assertEqual(self.client.get(f'/teacher-access/student/{self.grant.id}/').status_code, 200)
        make_teacher('teach2')
        self.client.login(username='teach2', password=PASSWORD)
        self.assertEqual(self.client.get(f'/teacher-access/student/{self.grant.id}/').status_code, 404)
