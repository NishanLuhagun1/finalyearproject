from django.test import TestCase

from spp_core.testing import PASSWORD, make_student
from .models import Goal


class GoalTests(TestCase):
    def setUp(self):
        self.user, self.student = make_student()
        self.client.login(username='stu', password=PASSWORD)

    def test_goals_page_renders_and_creates_goals(self):
        self.assertEqual(self.client.get('/students/goals/').status_code, 200)
        response = self.client.post('/students/goals/', {'title': 'Pass DBMS', 'target_date': '2030-01-01'})
        self.assertEqual(response.status_code, 302)
        self.assertContains(self.client.get('/students/goals/'), 'Pass DBMS')

    def test_toggle_and_delete_require_post(self):
        goal = Goal.objects.create(student=self.student, title='g')
        self.assertEqual(self.client.get(f'/students/goals/{goal.id}/toggle/').status_code, 405)
        self.assertEqual(self.client.get(f'/students/goals/{goal.id}/delete/').status_code, 405)
        goal.refresh_from_db()
        self.assertFalse(goal.is_completed)

        self.client.post(f'/students/goals/{goal.id}/toggle/')
        goal.refresh_from_db()
        self.assertTrue(goal.is_completed)
        self.client.post(f'/students/goals/{goal.id}/delete/')
        self.assertFalse(Goal.objects.filter(id=goal.id).exists())

    def test_cannot_touch_another_students_goal(self):
        _, other = make_student('other', 'S002')
        goal = Goal.objects.create(student=other, title='theirs')
        self.assertEqual(self.client.post(f'/students/goals/{goal.id}/delete/').status_code, 404)
        self.assertTrue(Goal.objects.filter(id=goal.id).exists())

    def test_dashboard_links_to_a_working_goals_page(self):
        response = self.client.get('/accounts/dashboard/')
        self.assertContains(response, '/students/goals/')
        self.assertEqual(self.client.get('/students/goals/').status_code, 200)
