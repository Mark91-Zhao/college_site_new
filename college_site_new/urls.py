from django.contrib import admin
from django.urls import path, include
from portal import views as portal_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),

    # Custom Authentication
    path("accounts/login/", portal_views.login_view, name="login"),
    path("accounts/logout/", portal_views.logout_view, name="logout"),

    # Password Reset Workflow
    path("accounts/password_reset/", auth_views.PasswordResetView.as_view(
        template_name="portal/password_reset.html",
        email_template_name="registration/password_reset_email.txt",
        html_email_template_name="registration/password_reset_email.html",
        subject_template_name="registration/password_reset_subject.txt"
    ), name="password_reset"),
    path("accounts/password_reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="portal/password_reset_done.html"
    ), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="portal/password_reset_confirm.html"
    ), name="password_reset_confirm"),
    path("accounts/reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="portal/password_reset_complete.html"
    ), name="password_reset_complete"),

    # Portal App
    path("", include("portal.urls")),
]
