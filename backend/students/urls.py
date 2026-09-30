from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='student_profile'),
    path('goals/', views.goal_list_view, name='goal_list'),
    path('goals/<int:goal_id>/toggle/', views.toggle_goal_view, name='toggle_goal'),
    path('goals/<int:goal_id>/delete/', views.delete_goal_view, name='delete_goal'),
]