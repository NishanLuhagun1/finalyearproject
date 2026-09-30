from django.contrib import admin
from .models import Subject, Result

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'course', 'semester')
    list_filter = ('course', 'semester')

admin.site.register(Result)