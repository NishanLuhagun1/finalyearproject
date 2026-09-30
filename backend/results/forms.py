from django import forms
from .models import Subject, StudentSubject


class StudentSubjectForm(forms.ModelForm):
    subject = forms.ModelChoiceField(queryset=Subject.objects.none())

    class Meta:
        model = StudentSubject
        fields = ['subject', 'semester']

    def __init__(self, *args, student=None, semester=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.student = student
        # Show every subject in the student's course -- semester placement
        # varies by university, so the student decides which semester they're
        # taking a subject in via the semester field, not a fixed curriculum.
        queryset = Subject.objects.all()
        if student is not None and student.course is not None:
            queryset = queryset.filter(course=student.course)
        self.fields['subject'].queryset = queryset.order_by('name')

    def clean(self):
        cleaned = super().clean()
        subject, semester = cleaned.get('subject'), cleaned.get('semester')
        # `student` isn't a form field, so ModelForm's own unique_together
        # check skips it -- without this the DB constraint raises a 500.
        if self.student and subject and semester and StudentSubject.objects.filter(
            student=self.student, subject=subject, semester=semester
        ).exists():
            raise forms.ValidationError(f"You have already added {subject.name} to Semester {semester}.")
        return cleaned
