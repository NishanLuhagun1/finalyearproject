from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_access_view, name='manage_teacher_access'),
    path('join/', views.join_invite_view, name='join_teacher_invite'),
    path('accept/<str:token>/', views.accept_invite_view, name='accept_teacher_invite'),
    path('my-students/', views.my_students_view, name='my_students'),
    path('student/<int:grant_id>/', views.student_detail_view, name='teacher_student_detail'),
]
