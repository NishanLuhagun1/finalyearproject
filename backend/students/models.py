from django.db import models
from accounts.models import Profile

class Course(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True)
    contact = models.CharField(max_length=20, blank=True)
    college_name = models.CharField(max_length=150, blank=True)
    career_goal = models.CharField(max_length=100, blank=True)
    interest_area = models.CharField(max_length=100, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def __str__(self):
        return self.full_name


class Goal(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=150)
    target_date = models.DateField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.title}"