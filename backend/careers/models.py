from django.db import models
from students.models import Student

class CareerProfile(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    min_predicted_score = models.FloatField()
    required_subjects = models.TextField(help_text="Comma-separated key subjects")
    required_soft_skills = models.TextField(help_text="Comma-separated key soft skills")
    required_technical_skills = models.TextField(blank=True, help_text="Comma-separated technical skill fields")
    required_programming_languages = models.TextField(blank=True, help_text="Comma-separated languages")
    min_study_time = models.IntegerField(null=True, blank=True, help_text="1-4 scale, matching SemesterStudyTime")

    def __str__(self):
        return self.name


class CareerAssessment(models.Model):
    INTEREST_CHOICES = [
        ('software_engineering', 'Software Engineering'),
        ('data_analytics', 'Data Analytics'),
        ('ui_ux_design', 'UI/UX Design'),
        ('network_administration', 'Network Administration'),
        ('business_analysis', 'Business Analysis'),
        ('cybersecurity', 'Cybersecurity'),
        ('cloud_computing', 'Cloud Computing'),
        ('mobile_development', 'Mobile App Development'),
        ('artificial_intelligence', 'Artificial Intelligence / Machine Learning'),
        ('game_development', 'Game Development'),
        ('project_management', 'IT Project Management'),
        ('quality_assurance', 'Quality Assurance / Testing'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='career_assessments')
    interest_area = models.CharField(max_length=100, choices=INTEREST_CHOICES, blank=True)
    communication_skill = models.IntegerField(null=True, blank=True)
    teamwork_skill = models.IntegerField(null=True, blank=True)
    problem_solving_skill = models.IntegerField(null=True, blank=True)
    leadership_skill = models.IntegerField(null=True, blank=True)
    adaptability_skill = models.IntegerField(null=True, blank=True)
    time_management_skill = models.IntegerField(null=True, blank=True)
    critical_thinking_skill = models.IntegerField(null=True, blank=True)
    creativity_skill = models.IntegerField(null=True, blank=True)
    programming_skill = models.IntegerField(null=True, blank=True)
    database_skill = models.IntegerField(null=True, blank=True)
    web_dev_skill = models.IntegerField(null=True, blank=True)
    networking_skill = models.IntegerField(null=True, blank=True)
    programming_languages = models.CharField(max_length=255, blank=True, help_text="Comma-separated languages known")
    assessed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - Career Assessment {self.assessed_at.date()}"


class CareerSuggestion(models.Model):
    assessment = models.ForeignKey(CareerAssessment, on_delete=models.CASCADE, related_name='suggestions')
    career = models.ForeignKey(CareerProfile, on_delete=models.CASCADE)
    match_score = models.FloatField()
    gap_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.assessment.student.full_name} - {self.career.name}"


def get_assessment(student, create=False):
    """The student's career assessment (oldest first if duplicates exist).

    Views must go through this rather than get_or_create(), which raises
    MultipleObjectsReturned as soon as a student has more than one row.
    """
    assessment = CareerAssessment.objects.filter(student=student).order_by('pk').first()
    if assessment is None and create:
        assessment = CareerAssessment.objects.create(student=student)
    return assessment
