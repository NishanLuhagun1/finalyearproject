"""Small helpers shared by the app test modules."""
from django.contrib.auth.models import User

from students.models import Course, Student

PASSWORD = 'Xy!9pqLmn#22'


def make_student(username='stu', student_id='S001', course='BIT'):
    user = User.objects.create_user(username, password=PASSWORD)
    student = Student.objects.create(
        profile=user.profile, student_id=student_id, full_name=username.title(),
        course=Course.objects.get(name=course),
    )
    return user, student


def make_teacher(username='teach'):
    user = User.objects.create_user(username, password=PASSWORD)
    user.profile.role = 'teacher'
    user.profile.save()
    return user
