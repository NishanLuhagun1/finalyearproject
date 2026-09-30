from django.contrib import admin
from .models import CareerProfile, CareerAssessment, CareerSuggestion

admin.site.register(CareerProfile)
admin.site.register(CareerAssessment)
admin.site.register(CareerSuggestion)