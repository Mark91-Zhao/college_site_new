from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.student_register, name="register"),
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("staff/profile/", views.staff_profile, name="staff_profile"),
    path("staff/profile/update/<int:pk>/", views.staff_update, name="staff_update"),
    path("students/", views.student_list, name="student_list"),
    path("students/create/", views.student_create, name="student_create"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/update/", views.student_update_staff, name="student_update_staff"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path("courses/", views.course_list, name="course_list"),
    path("courses/create/", views.course_create, name="course_create"),
    path("courses/<int:pk>/update/", views.course_update, name="course_update"),
    path("courses/<int:pk>/delete/", views.course_delete, name="course_delete"),
    path("student/results/", views.student_results, name="student_results"),
    path("staff/add-result/<int:student_id>/<int:semester_id>/", views.add_result, name="add_result"),
    path("staff/add-result/semester/<int:semester_id>/", views.add_result_semester, name="add_result_semester"),
    path("staff/add-semester-gpa/<int:student_id>/<int:semester_id>/", views.add_semester_gpa, name="add_semester_gpa"),
    path("upload-results/", views.upload_results, name="upload_results"),
    path("download-template/", views.download_results_template, name="download_results_template"),
    path("staff/export-excel/", views.export_excel, name="export_excel"),
    path("transcript/", views.transcript, name="transcript"),
    path("transcript/pdf/", views.export_transcript_pdf, name="export_transcript_pdf"),
    path("student/login/", views.student_login, name="student_login"),
    path("staff/login/", views.staff_login, name="staff_login"),
    path("get_courses/<int:semester_id>/", views.get_courses_by_semester, name="get_courses_by_semester"),
    path("student/update/<int:pk>/", views.student_update_self, name="student_update_self"),
    
    # FIX FOR LOGOUT
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
]