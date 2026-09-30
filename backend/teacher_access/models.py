import secrets
from django.db import models
from accounts.models import Profile
from students.models import Student


def generate_token():
    return secrets.token_urlsafe(24)


class TeacherAccessGrant(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='teacher_grants')
    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True, related_name='student_grants')
    invite_token = models.CharField(max_length=64, unique=True, default=generate_token)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = "active" if self.is_active else "pending"
        teacher_name = self.teacher.user.username if self.teacher else "unclaimed"
        return f"{self.student.full_name} -> {teacher_name} ({status})"