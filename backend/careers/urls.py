from django.urls import path
from . import views

urlpatterns = [
    path('interest/', views.add_interest_view, name='add_interest'),
    path('soft-skills/', views.add_soft_skills_view, name='add_soft_skills'),
    path('roadmap/', views.roadmap_view, name='career_roadmap'),

]