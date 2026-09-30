from django.db import models
from students.models import Student, Course

class Subject(models.Model):
    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, related_name='subjects')
    semester = models.IntegerField(choices=SEMESTER_CHOICES, null=True, blank=True, help_text="Semester this subject is normally taught in")

    def __str__(self):
        return self.name


class StudentSubject(models.Model):
    SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='subjects_taken')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'semester')

    def __str__(self):
        return f"{self.student.full_name} - {self.subject.name} (Sem {self.semester})"


class Result(models.Model):
    EXAM_TYPE_CHOICES = [
        ('midterm', 'Midterm'),
        ('preboard', 'Preboard'),
    ]

    student_subject = models.ForeignKey(StudentSubject, on_delete=models.CASCADE, related_name='results')
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES)
    assignment_score = models.FloatField()
    exam_score = models.FloatField()
    attendance_percent = models.FloatField()
    weighted_score = models.FloatField(null=True, blank=True)
    predicted_score = models.FloatField(null=True, blank=True)
    is_eligible = models.BooleanField(default=False)
    entered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_subject} - {self.exam_type}"


class SemesterStudyTime(models.Model):
    STUDY_TIME_CHOICES = [
        (1, 'Less than 2 hours/week'),
        (2, '2 to 5 hours/week'),
        (3, '5 to 10 hours/week'),
        (4, 'More than 10 hours/week'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='study_times')
    semester = models.IntegerField(choices=StudentSubject.SEMESTER_CHOICES)
    study_time = models.IntegerField(choices=STUDY_TIME_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')

    def __str__(self):
        return f"{self.student.full_name} - Semester {self.semester} study time"