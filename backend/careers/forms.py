from django import forms
from .models import CareerAssessment

PROGRAMMING_LANGUAGE_CHOICES = [
    ('Python', 'Python'),
    ('Java', 'Java'),
    ('JavaScript', 'JavaScript'),
    ('C++', 'C++'),
    ('C#', 'C#'),
    ('PHP', 'PHP'),
    ('SQL', 'SQL'),
    ('HTML', 'HTML'),
    ('CSS', 'CSS'),
]


class InterestAreaForm(forms.ModelForm):
    class Meta:
        model = CareerAssessment
        fields = ['interest_area']


class SoftSkillsForm(forms.ModelForm):
    programming_languages = forms.MultipleChoiceField(
        choices=PROGRAMMING_LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = CareerAssessment
        fields = ['communication_skill', 'teamwork_skill', 'problem_solving_skill',
                  'leadership_skill', 'adaptability_skill', 'time_management_skill',
                  'critical_thinking_skill', 'creativity_skill',
                  'programming_skill', 'database_skill', 'web_dev_skill', 'networking_skill',
                  'programming_languages']
        widgets = {
            field: forms.NumberInput(attrs={
                'type': 'range', 'min': 1, 'max': 5,
                'oninput': 'this.nextElementSibling.textContent=this.value',
            })
            for field in [
                'communication_skill', 'teamwork_skill', 'problem_solving_skill',
                'leadership_skill', 'adaptability_skill', 'time_management_skill',
                'critical_thinking_skill', 'creativity_skill',
                'programming_skill', 'database_skill', 'web_dev_skill', 'networking_skill',
            ]
        }

    SKILL_FIELDS = [
        'communication_skill', 'teamwork_skill', 'problem_solving_skill',
        'leadership_skill', 'adaptability_skill', 'time_management_skill',
        'critical_thinking_skill', 'creativity_skill',
        'programming_skill', 'database_skill', 'web_dev_skill', 'networking_skill',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.SKILL_FIELDS:
            if self.initial.get(field) is None:
                self.initial[field] = 3
        if self.instance and self.instance.pk and self.instance.programming_languages:
            self.fields['programming_languages'].initial = [
                lang.strip() for lang in self.instance.programming_languages.split(',') if lang.strip()
            ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.programming_languages = ','.join(self.cleaned_data.get('programming_languages', []))
        if commit:
            instance.save()
        return instance