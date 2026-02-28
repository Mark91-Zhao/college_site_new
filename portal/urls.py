from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [

    # =========================
    # HOME & AUTHENTICATION
    # =========================
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # =========================
    # STUDENT ROUTES
    # =========================
    path("student/register/", views.student_register, name="student_register"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),

    # =========================
    # STAFF ROUTES
    # =========================
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/add-result/", views.add_result, name="add_result"),
    path("upload-results/", views.upload_results, name="upload_results"),
    path("download-template/", views.download_results_template, name="download_results_template"),

    # =========================
    # TRANSCRIPT & EXPORT
    # =========================
    path("transcript/", views.transcript, name="transcript"),
    path("transcript/pdf/", views.export_transcript_pdf, name="export_transcript_pdf"),
]