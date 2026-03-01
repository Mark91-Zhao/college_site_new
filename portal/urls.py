"""
portal/urls.py
Complete URL Configuration
Using Django Built-in Authentication
"""

from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================
    path("", views.home, name="home"),

    # =====================================================
    # STUDENT SELF REGISTRATION
    # =====================================================
    path("register/", views.student_register, name="register"),

    # =====================================================
    # DASHBOARDS
    # =====================================================
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),

    # =====================================================
    # USER PROFILES
    # =====================================================
    path("student/profile/", views.student_profile, name="student_profile"),
    path("staff/profile/", views.staff_profile, name="staff_profile"),

    # =====================================================
    # STUDENT MANAGEMENT (STAFF ONLY)
    # =====================================================
    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.student_create, name="student_create"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/update/", views.student_update, name="student_update"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),

    # =====================================================
    # COURSE MANAGEMENT (STAFF ONLY)
    # =====================================================
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/update/", views.course_update, name="course_update"),
    path("courses/<int:pk>/delete/", views.course_delete, name="course_delete"),

    # =====================================================
    # ACADEMIC OPERATIONS
    # =====================================================
    path("staff/add-result/", views.add_result, name="add_result"),
    path("upload-results/", views.upload_results, name="upload_results"),
    path("download-template/", views.download_results_template, name="download_results_template"),

    # =====================================================
    # TRANSCRIPTS
    # =====================================================
    path("transcript/", views.transcript, name="transcript"),
    path("transcript/pdf/", views.export_transcript_pdf, name="export_transcript_pdf"),
]