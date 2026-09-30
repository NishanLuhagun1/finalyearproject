from django import forms
from .models import Goal, Student


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['title', 'target_date']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date'}),
        }


class StudentCourseForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['course']