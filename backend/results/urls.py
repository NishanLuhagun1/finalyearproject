from django.urls import path
from . import views

urlpatterns = [
    path('add-subject/', views.add_subject_view, name='add_subject'),
    path('add-marks/', views.add_marks_view, name='add_marks'),
    path('score-summary/', views.score_summary_view, name='score_summary'),
    path('analytics/', views.analytics_view, name='analytics'),
]
