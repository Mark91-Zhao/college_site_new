from django.urls import path
from . import views

# Namespace for all exams URLs
app_name = "exams"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/", views.register_student, name="register_student"),
    path("student_login/", views.student_login, name="student_login"),
    path("staff_login/", views.staff_login, name="staff_login"),
    path("logout/", views.user_logout, name="logout"),
    path("add_result/", views.add_result, name="add_result"),
    path("student_results/", views.student_results, name="student_results"),
    path("upload/", views.upload_file, name="upload"),
    path("csrf_debug/", views.csrf_debug, name="csrf_debug"),
]
