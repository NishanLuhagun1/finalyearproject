from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from students.models import Course, Student


class StudentRegistrationForm(UserCreationForm):
    ROLE_CHOICES = [('student', 'Student'), ('teacher', 'Teacher')]

    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='student', widget=forms.RadioSelect)
    full_name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=200, required=False)
    contact = forms.CharField(max_length=20, required=False)
    college_name = forms.CharField(max_length=150, required=False)
    # Only needed for students; enforced in clean() so teachers can register too.
    student_id = forms.CharField(max_length=20, required=False)
    course = forms.ModelChoiceField(queryset=Course.objects.all(), required=False, empty_label="Select your course")

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('role') == 'student':
            student_id = (cleaned.get('student_id') or '').strip()
            if not student_id:
                self.add_error('student_id', 'Student ID is required.')
            elif Student.objects.filter(student_id=student_id).exists():
                self.add_error('student_id', 'A student with this ID is already registered.')
            else:
                cleaned['student_id'] = student_id
            if not cleaned.get('course'):
                self.add_error('course', 'Please select your course.')
        return cleaned
